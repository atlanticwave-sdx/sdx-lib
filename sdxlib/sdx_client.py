# sdx_client.py

import logging
import requests
from typing import Optional, List, Dict

from sdxlib.sdx_token_auth import TokenAuthentication
from sdxlib.sdx_exception import SDXException
from sdxlib.sdx_validator import SDXValidator
from sdxlib.sdx_request import _make_request, _get_headers, _build_payload


class SDXClient:
    """Client for interacting with the AtlanticWave-SDX L2VPN API."""

    VERSION = "1.0"

    def __init__(self, url_env: str = "test", source: str = "fabric", logger: Optional[logging.Logger] = None) -> None:
        self.base_url = SDXValidator.validate_required_url_env(url_env, "test")
        self._logger = logger or logging.getLogger(__name__)
        self._request_cache = {}
        self.token_auth = TokenAuthentication().load_token()

        self.source = source
        self.user_id = None
        self.ownership = None
        self.email = None

        self.name = None
        self.endpoints = None
        self.description = None
        self.notifications = None
        self.scheduling = None
        self.qos_metrics = None

        self.create_user_session()

    def create_user_session(self, source: str = "fabric") -> None:
        """Authenticate the user session and fetch user data from /login."""
        try:
            sub = self.token_auth.token_sub
            ownership = SDXValidator.validate_ownership(sub)
            email = self.token_auth.token_decoded.get("email")
            eppn = self.token_auth.token_eppn
            given_name = self.token_auth.token_given_name
            family_name = self.token_auth.token_family_name
        except Exception as e:
            raise SDXException(
                status_code=401,
                message="Token or ownership derivation failed",
                error_details=str(e),
            )

        payload = {
            "source": source,
            "ownership": ownership,
            "email": email or "",
            "eppn": eppn or "",
            "first_name": given_name or "",
            "last_name": family_name or "",
            "role": "researcher",
        }

        url = f"{self.base_url.rsplit('/', 1)[0]}/login/"
        response, status_code = _make_request("POST", url, _get_headers(self), payload, "session login")

        if not isinstance(response, dict):
            raise SDXException(status_code=500, message="Invalid response format", error_details=str(response))
        if status_code != 200:
            raise SDXException(status_code=status_code, message="Session login failed", error_details=response)

        self.user_id = response.get("user_id")
        self.ownership = response.get("ownership", ownership)
        self.email = response.get("email", payload["email"])
        self.source = source

    def services(self, method: str = "GET", service_id: Optional[str] = None, delete: bool = False, data: Optional[dict] = None) -> tuple:
        """Handles GET, POST, DELETE to /services."""
        if not self.user_id or not self.ownership:
            return 403, None, "No session or ownership set."

        url = f"{self.base_url.rsplit('/', 1)[0]}/services/"
        headers = _get_headers(self)
        payload = {
            "user_id": self.user_id,
            "ownership": self.ownership,
            "email": self.email,
            "source": self.source,
        }

        if service_id:
            payload["service_id"] = service_id
        if data:
            payload.update(data)

        if method == "GET":
            return _make_request("GET", url, headers, payload, "get services")
        elif method == "POST":
            return _make_request("POST", url, headers, payload, "create service")
        elif method == "DELETE":
            return _make_request("DELETE", url, headers, payload, "delete service")
        else:
            return 400, None, f"Unsupported method: {method}"

    def create_l2vpn(self, name: str, endpoints: List[Dict[str, str]]) -> dict:
        """Creates an L2VPN if the user has permission."""
        if not SDXValidator.validate_user_permissions(self._logger, self.user_id, self.ownership, self.services):
            return {"status_code": 403, "data": None, "error": "User is not authenticated or lacks permissions."}

        self.name = SDXValidator.validate_name(name)
        self.endpoints = SDXValidator.validate_endpoints(endpoints)
        SDXValidator.validate_required_attributes(self.base_url, self.name, self.endpoints)

        url = f"{self.base_url}/l2vpn/{self.VERSION}"
        payload = _build_payload(self)

        cache_key = (self.name, tuple(endpoint.get("port_id", "") for endpoint in self.endpoints))
        if cache_key in self._request_cache:
            return {
                "status_code": 200,
                "data": {"service_id": self._request_cache[cache_key][1].get("service_id")},
                "error": None,
            }

        response, status_code = _make_request("POST", url, _get_headers(self), payload, "create L2VPN", cache_key)
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}

    def update_l2vpn(self, service_id: str, **kwargs) -> dict:
        """Updates an L2VPN's attributes like state or description."""
        if not SDXValidator.validate_user_permissions(self._logger, self.user_id, self.ownership, self.services, service_id):
            return {"status_code": 403, "data": None, "error": "Permission denied for updating L2VPN."}

        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"

        if "state" in kwargs:
            if kwargs["state"].lower() not in ["enabled", "disabled"]:
                return {"status_code": 400, "data": None, "error": "Invalid state. Must be 'enabled' or 'disabled'."}
            kwargs["state"] = kwargs["state"].lower()

        payload = {k: v for k, v in kwargs.items() if v is not None}
        payload["service_id"] = service_id

        response, status_code = _make_request("PATCH", url, _get_headers(self), payload, "update L2VPN")
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}

    def delete_l2vpn(self, service_id: str) -> dict:
        """Deletes an L2VPN if the user owns it."""
        if not SDXValidator.validate_user_permissions(self._logger, self.user_id, self.ownership, self.services, service_id):
            return {"status_code": 403, "data": None, "error": "Permission denied for deleting L2VPN."}

        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"
        response, status_code = _make_request("DELETE", url, _get_headers(self), operation="delete L2VPN")
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}

    def get_topology(self) -> dict:
        """Retrieves SDX network topology."""
        url = f"{self.base_url}/topology/{self.VERSION}"
        response, status_code = _make_request("GET", url, _get_headers(self), operation="get topology")
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}

    def get_available_ports(self) -> dict:
        """Returns list of available ports."""
        topology_result = self.get_topology()
        ports = []
        if topology_result["status_code"] == 200 and isinstance(topology_result["data"], dict):
            ports = topology_result["data"].get("ports", [])
        return {"status_code": topology_result["status_code"], "data": ports, "error": topology_result["error"]}

    def get_all_l2vpns(self) -> dict:
        """Returns all L2VPNs from the controller."""
        url = f"{self.base_url}/l2vpn/{self.VERSION}"
        response, status_code = _make_request("GET", url, _get_headers(self), operation="get all L2VPNs")
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}


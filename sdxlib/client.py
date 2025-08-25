# sdx_client.py

import logging
import pandas as pd
from typing import Optional, List, Dict, Union, Any

from sdxlib.config import BASE_URL
from sdxlib.exception import SDXException
from sdxlib.validator import SDXValidator
from sdxlib.request import _make_request
from sdxlib.session import create_user_session, manage_services
from sdxlib.response import SDXResponse


class SDXClient:
    """Client for interacting with the AtlanticWave-SDX L2VPN API."""
    VERSION = "1.0"

    def __init__(self, url_env: str = "test", source: str = "fabric", logger: Optional[logging.Logger] = None) -> None:
        self.url = SDXValidator.validate_required_url(BASE_URL, url_env)
        self._logger = logger or logging.getLogger(__name__)
        self._request_cache = {}

        self.token_auth = TokenAuth().load_token()
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

        self._initialize_user_session()

    def _initialize_user_session(self) -> None:
        """Initialize user session and populate client attributes."""
        session = create_user_session(self, BASE_URL, self.source)
        self.user_id = session["user_id"]
        self.ownership = session["ownership"]
        self.email = session["email"]

    def services(self, method: str = "GET", service_id: Optional[str] = None, delete: bool = False, data: Optional[dict] = None) -> tuple:
        return manage_services(self, method, service_id, data)

    def create_l2vpn(self, name: str, endpoints: List[Dict[str, str]]) -> dict:
        if not SDXValidator.has_permission(self._logger, self.user_id, self.ownership, self.services):
            return {"status_code": 403, "data": None, "error": "User is not authenticated or lacks permissions."}

        self.name = SDXValidator.validate_name(name)
        self.endpoints = SDXValidator.validate_endpoints(endpoints)
        SDXValidator.validate_required_attributes(self.url, self.name, self.endpoints)

        url = f"{self.url}/l2vpn/{self.VERSION}"
        payload = {
            key: value for key, value in {
                "name": self.name,
                "endpoints": self.endpoints,
                "ownership": self.ownership,
                "description": self.description,
                "notifications": self.notifications,
                "scheduling": self.scheduling,
                "qos_metrics": self.qos_metrics,
            }.items() if value is not None  # Exclude None values
        }   

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
        if not SDXValidator.has_permission(self._logger, self.user_id, self.ownership, self.services, service_id):
            return {"status_code": 403, "data": None, "error": "Permission denied for updating L2VPN."}

        url = f"{self.url}/l2vpn/{self.VERSION}/{service_id}"

        if "state" in kwargs:
            if kwargs["state"].lower() not in ["enabled", "disabled"]:
                return {"status_code": 400, "data": None, "error": "Invalid state. Must be 'enabled' or 'disabled'."}
            kwargs["state"] = kwargs["state"].lower()

        payload = {k: v for k, v in kwargs.items() if v is not None}
        payload["service_id"] = service_id

        response, status_code = _make_request("PATCH", url, _get_headers(self), payload, "update L2VPN")
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}

    def delete_l2vpn(self, service_id: str) -> dict:
        if not SDXValidator.has_permission(self._logger, self.user_id, self.ownership, self.services, service_id):
            return {"status_code": 403, "data": None, "error": "Permission denied for deleting L2VPN."}

        url = f"{self.url}/l2vpn/{self.VERSION}/{service_id}"
        response, status_code = _make_request("DELETE", url, _get_headers(self), operation="delete L2VPN")
        return {"status_code": status_code, "data": response, "error": None if status_code == 200 else str(response)}

    def get_l2vpn(self, service_id: str, format: str = "dataframe") -> Union[pd.DataFrame, Dict[str, Any], None]:
        url = f"{self.url}/l2vpn/{self.VERSION}/{service_id}"
        response, status_code = _make_request("GET", url, _get_headers(self), operation="retrieve L2VPN")

        if status_code != 200 or not isinstance(response, dict):
            self._logger.warning(f"L2VPN with ID {service_id} not found or invalid response.")
            return None

        l2vpn_data = response.get(service_id) if service_id in response else response

        if not l2vpn_data:
            self._logger.warning(f"No L2VPN data found for service ID: {service_id}")
            return None

        name = l2vpn_data.get("name", "Unknown")
        ownership = l2vpn_data.get("ownership", "Unknown")
        endpoints = [
            {"port_id": ep.get("port_id", "Unknown"), "vlan": ep.get("vlan", "Unknown")}
            for ep in l2vpn_data.get("endpoints", [])
        ]
        notifications = ", ".join(
            str(n.get("email", "Unknown")) if isinstance(n, dict) else str(n)
            for n in l2vpn_data.get("notifications", [])
        )
        scheduling = str(l2vpn_data.get("scheduling") or "None")
        qos_metrics = str(l2vpn_data.get("qos_metrics") or "None")

        if format == "dataframe":
            return pd.DataFrame([
                {
                    "Service ID": service_id,
                    "Name": name,
                    "Port ID": ep["port_id"],
                    "VLAN": ep["vlan"],
                    "Endpoints": str(endpoints),
                    "Ownership": ownership,
                    "Notifications": notifications,
                    "Scheduling": scheduling,
                    "QoS Metrics": qos_metrics,
                }
                for ep in endpoints
            ])

        return {
            "Service ID": service_id,
            "Name": name,
            "Endpoints": endpoints,
            "Ownership": ownership,
            "Notifications": notifications,
            "Scheduling": scheduling,
            "QoS Metrics": qos_metrics,
        }

    def get_all_l2vpns(
        self,
        archived: bool = False,
        format: str = "dataframe",
        search: Optional[str] = None
    ) -> Union[pd.DataFrame, List[Dict[str, Any]], None]:
        url = f"{self.url}/l2vpn/{self.VERSION}/archived" if archived else f"{self.url}/l2vpn/{self.VERSION}"
        response, status_code = _make_request("GET", url, _get_headers(self), operation="retrieve all L2VPNs")

        if status_code != 200 or not response:
            self._logger.warning("No L2VPNs retrieved or invalid response.")
            return pd.DataFrame() if format == "dataframe" else []

        if not isinstance(response, dict):
            self._logger.warning(f"Expected dict, got {type(response).__name__}: {response}")
            return pd.DataFrame() if format == "dataframe" else []

        l2vpns = {
            sid: SDXResponse(data)
            for sid, data in response.items()
        }

        if search:
            search = search.lower()
            l2vpns = {
                sid: l2vpn for sid, l2vpn in l2vpns.items()
                if search in sid.lower() or search in (l2vpn.name or "").lower()
            }

        if not l2vpns:
            self._logger.info("No L2VPNs matched the filter.")
            return pd.DataFrame() if format == "dataframe" else []

        formatted = []
        for sid, l2vpn in l2vpns.items():
            formatted.append({
                "Service ID": sid,
                "Name": l2vpn.name,
                "Endpoints": [
                    {"port_id": ep.get("port_id", "Unknown"), "vlan": ep.get("vlan", "Unknown")}
                    for ep in l2vpn.endpoints
                ],
                "Ownership": l2vpn.ownership,
                "Notifications": ", ".join(
                    n.get("email", "Unknown") if isinstance(n, dict) else str(n)
                    for n in l2vpn.notifications
                ),
                "Scheduling": str(l2vpn.scheduling or "None"),
                "QoS Metrics": str(l2vpn.qos_metrics or "None"),
            })

        return pd.DataFrame(formatted) if format == "dataframe" else formatted


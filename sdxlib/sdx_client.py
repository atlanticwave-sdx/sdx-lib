import logging
import pandas as pd
import re
import requests
from collections import defaultdict
from typing import Optional, List, Dict, Union, Any
from requests.exceptions import RequestException, HTTPError, Timeout
from sdxlib.sdx_token_auth import TokenAuthentication
from sdxlib.sdx_exception import SDXException
from sdxlib.sdx_response import SDXResponse
from sdxlib.sdx_validator import SDXValidator


class SDXClient:
    """Client for interacting with the AtlanticWave-SDX L2VPN API."""

    VERSION = "1.0"

    def __init__(
        self,
        base_url: str,
        name: Optional[str] = None,
        endpoints: Optional[List[Dict[str, str]]] = None,
        ownership: Optional[str] = None,
        description: Optional[str] = None,
        notifications: Optional[List[Dict[str, str]]] = None,
        scheduling: Optional[Dict[str, str]] = None,
        qos_metrics: Optional[Dict[str, Dict[str, Union[int, bool]]]] = None,
        fabric_token: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize SDXClient instance."""
        self.base_url = SDXValidator.validate_non_empty_string(base_url, "Base URL")
        self.name = SDXValidator.validate_name(name)
        self.endpoints = SDXValidator.validate_endpoints(endpoints)
        self.ownership = (
            ownership if ownership is not None
            else TokenAuthentication().load_token().token_sub
        )
        self.ownership = SDXValidator.validate_ownership(self.ownership)
        self.description = SDXValidator.validate_description(description)
        self.notifications = (
            notifications if notifications is not None
            else [{"email": TokenAuthentication().load_token().token_eppn}]
        )
        self.notifications = SDXValidator.validate_notifications(self.notifications)
        self.scheduling = SDXValidator.validate_scheduling(scheduling)
        self.qos_metrics = SDXValidator.validate_qos_metrics(qos_metrics)
        self.fabric_token = fabric_token or TokenAuthentication().load_token().fabric_token
        self._logger = logger or logging.getLogger(__name__)
        self._request_cache = {}

    def create_l2vpn(self) -> dict:
        """Creates an L2VPN."""
        # Perform validation using SDXValidator
        SDXValidator.validate_required_attributes(self.base_url, self.name, self.endpoints)

        url = f"{self.base_url}/l2vpn/{self.VERSION}"
        payload = self._build_payload()

        # Generate cache key safely
        cache_key = (
            self.name,
            tuple(endpoint.get("port_id", "") for endpoint in self.endpoints)
        )
        if cache_key in self._request_cache:
            return {
                "service_id": self._request_cache[cache_key][1].get("service_id")
            }

        return self._make_request(
            "POST", url, self._get_headers(), payload, "create L2VPN", cache_key
        )

    def update_l2vpn(self, service_id: str, **kwargs) -> dict:
        """ Updates an existing L2VPN."""
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"

        if "state" in kwargs:
            if kwargs["state"].lower() not in ["enabled", "disabled"]:
                raise ValueError("State must be 'enabled' or 'disabled'.")
            kwargs["state"] = kwargs["state"].lower()

        payload = {k: v for k, v in kwargs.items() if v is not None}
        payload["service_id"] = service_id

        return self._make_request("PATCH", url, self._get_headers(), payload)

    def delete_l2vpn(self, service_id: str) -> Optional[Dict]:
        """ Deletes an L2VPN using the provided L2VPN ID. """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"

        return self._make_request(
            "DELETE", url, self._get_headers(), operation="delete L2VPN")

    def _parse_vlan_value(self, vlan_value: str) -> List[int]:
        """ Parses VLAN values from a string representation. """
        if ":" in vlan_value:
            try:
                start, end = map(int, vlan_value.split(":"))
                return list(range(start, end + 1))
            except ValueError:
                self._logger.warning(f"Invalid VLAN range: {vlan_value}")
        return [int(vlan_value)] if vlan_value.isdigit() else []
        
    def _get_vlans_in_use(self) -> Dict[str, List[int]]:
        """ Retrieves VLANs in use across all active L2VPNs. """
        vlan_usage = defaultdict(set)
        
        try:
            l2vpns = self.get_all_l2vpns(format="json")

            if not l2vpns:  # Handle None or empty case
                self._logger.warning("No L2VPN data retrieved.")
                return {}
            
            if isinstance(l2vpns, list):  # Convert list to dict for compatibility
                l2vpns = {vpn["Service ID"]: vpn for vpn in l2vpns}
            
            for l2vpn in l2vpns.values():
                for endpoint in l2vpn.get("endpoints", []):
                    port_id, vlan = endpoint.get("port_id"), endpoint.get("vlan")
                    if port_id and vlan:
                        vlan_usage[port_id].update(self._parse_vlan_value(vlan))
            return {port_id: sorted(vlans) for port_id, vlans in vlan_usage.items()}
        except SDXException as e:
            self._logger.error(f"Error retrieving VLAN usage: {e}")
            return {}

    def _get_vlan_range(self, port, vlans_in_use: Dict[str, List[int]]) -> str:
        """ Extracts VLAN availability range from the Port services attribute. """
        try:
            # Extract Port ID, use Unknown if missing
            port_id = port.get("id", "Unknown")
            services = port.get("services",{})
            vlan_data = services.get(
                "l2vpn-ptp", {}).get("vlan_range", [])
            in_use = set(vlans_in_use.get(port_id, []))

            if not (vlan_data and all(len(v) == 2 for v in vlan_data)):
                return "None"

            # Generate available VLANs excluding those in use
            available_vlans = sorted(
                set(v for start, 
                    end in vlan_data for v in range(start, end + 1)) - in_use
            )
            if not available_vlans:
                return "None"
                
            # Convert to range format
            ranges, start, end = [], available_vlans[0], available_vlans[0]
            for vlan in available_vlans[1:]:
                if vlan == end + 1:
                    end = vlan
                else:
                    ranges.append(f"{start}-{end}" if start != end else str(start))
                    start = end = vlan

            ranges.append(f"{start}-{end}" if start != end else str(start))
            return ", ".join(ranges)

        except Exception as e:
            self._logger.error(
                f"Error extracting VLAN range from port {port_id}: {e}")
            return "None"

    def _format_port(self, port: Dict[str, Any], vlan_usage: Dict[str, List[int]]) -> Dict[str, str]:
        """ Formats port data with VLAN and entity details."""

        # Extract Port ID, use Unknown if missing
        port_id = port.get("id", "Unknown")

        # Extract Domain, Device, and Port Number using regex
        match = re.match(r"urn:sdx:port:(.*?):(.*?):(.*?)$", port_id)
        domain, device, port_number = match.groups() if match else ("Unknown", "Unknown", "Unknown")

        return {
            "Domain": domain,
            "Device": device,
            "Port": port_number,
            "Status": port.get("status", "Unknown"),
            "Port ID": port_id,
            "Entities": ", ".join(port.get("entities", []) or []),  
            "VLANs Available": self._get_vlan_range(port, vlan_usage),
            "VLANs in Use": "; ".join(map(str, vlan_usage.get(port_id, []))) or "None",  
        }

    def get_available_ports(
        self, format: str = "json", search: Optional[str] = None
        ) -> Union[pd.DataFrame, List[Dict[str, str]]]:
        """
        Fetches and returns available ports from the SDX topology, 
        with optional search filtering.
        """
        vlan_usage = self._get_vlans_in_use()
        topology_data = self._make_request(
            "GET", 
            f"{self.base_url}/topology", 
            self._get_headers(),
            operation="retrieve available ports"
        )
        
        # Extract available ports from topology data
        available_ports = []
        for node in topology_data.get("nodes", []):
            for port in node.get("ports", []):
                if port.get("status") == "up" and not port.get("nni"):
                    available_ports.append(self._format_port(port, vlan_usage))

        # Apply optional search filter
        if search:
            available_ports = [
                port for port in available_ports if search.lower() in port["Entities"].lower()
            ]

        # Print formatted table output with headers
        if available_ports:
            # Define column widths
            col_widths = [12, 12, 10, 8, 50, 50]  # Adjust for better spacing

            # Print headers
            headers = ["Domain", "Device", "Port", "Status", "Port ID", "Entities"]
            header_row = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
            separator = "-" * len(header_row)

            print(header_row)
            print(separator)

            # Print all matching ports
            for port in available_ports:
                row = " | ".join(f"{str(port[field]):<{col_widths[i]}}" for i, field in enumerate(headers))
                print(row)
        else:
            print(f"No ports found matching search term: '{search}'")
    
    def get_l2vpn(self, service_id: str, format: str = "dataframe") -> Union[pd.DataFrame, SDXResponse]:
        """
        Retrieves details of an existing L2VPN using the provided service ID.
        """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"


        response = self._make_request(
            "GET", url, self._get_headers(), operation="retrieve L2VPN")
        l2vpn_data = response.get(service_id)
    
        if not l2vpn_data:
            print(f"L2VPN with ID {service_id} not found.")
            return None

        sdx_response = SDXResponse(l2vpn_data)
        self.last_sdx_response = sdx_response  # Cache response

        # Extract relevant fields
        service_id = sdx_response.service_id
        name = sdx_response.name

        # Extract endpoint details
        endpoints = [
            {"port_id": ep.get("port_id", "Unknown"), "vlan": ep.get("vlan", "Unknown")}
            for ep in sdx_response.endpoints
        ]

        ownership = sdx_response.ownership

        notifications = ", ".join(
            str(n.get("email", "Unknown")) if isinstance(n, dict) else str(n) 
            for n in sdx_response.notifications
        )

        scheduling = str(sdx_response.scheduling or "None")
        qos_metrics = str(sdx_response.qos_metrics or "None")

        # Return JSON or DataFrame format
        if format == "dataframe":
            return pd.DataFrame([
                {"Service ID": service_id, "Name": name, "Port ID": ep["port_id"], "VLAN": ep["vlan"],
                 "Endpoints": str(endpoints), "Ownership": ownership, "Notifications": notifications,
                 "Scheduling": scheduling, "QoS Metrics": qos_metrics}
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
        self, archived: bool = False, format: str = "dataframe",
        search: Optional[str] = None
        ) -> Union[pd.DataFrame, Dict[str, SDXResponse]]:
        """
        Retrieves all L2VPNs, optionally filtered by service_id or name.
        """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/archived" if archived else f"{self.base_url}/l2vpn/{self.VERSION}"

        response = self._make_request(
            "GET", url, self._get_headers(), operation="retrieve all L2VPNs")

        if not response:
            print("No L2VPNs retrieved.")
            return pd.DataFrame() if format == "dataframe" else {}
        
        if not isinstance(response, dict):
            print(f"[get_all_l2vpns] Warning: Expected a dict, got {type(response).__name__}")
            print(f"Raw response: {response}")
            return {response}
        
        # Convert JSON response to SDXResponse objects
        l2vpns = {
            service_id: SDXResponse(
                l2vpn_data
            ) for service_id,l2vpn_data in response.items()
        }

        # Apply optional search filter
        if search:
            search = search.lower()
            l2vpns = {
                sid: l2vpn for sid, l2vpn in l2vpns.items()
                if search in sid.lower() or search in (l2vpn.name or "").lower()
            }
        
        if not l2vpns:
            print("No L2VPNs found.")
            return None

        formatted = [
            {
                "Service ID": sid,
                "Name": l2vpn.name,
                "Endpoints": [
                    {"port_id": endpoint.get("port_id", "Unknown"), "vlan": endpoint.get("vlan", "Unknown")}
                    for endpoint in l2vpn.endpoints
                ],
                "Ownership": l2vpn.ownership,
                "Notifications": ", ".join(
                    notification.get("email", "Unknown") if isinstance(notification, dict) else str(notification)
                    for notification in l2vpn.notifications
                ),
                "Scheduling": str(l2vpn.scheduling or "None"),
                "QoS Metrics": str(l2vpn.qos_metrics or "None")
            }
            for sid, l2vpn in l2vpns.items()
        ]

        if format == "dataframe":
            return pd.DataFrame(formatted)

        return formatted

    def _build_payload(self) -> dict:
        """ 
        Constructs payload for API requests, excluding None values.
        """
        return {
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

    def _get_headers(self) -> Dict[str, str]:
        """Returns headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.fabric_token}",
        }

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        payload: Optional[dict] = None,
        operation: str = "",
        cache_key: Optional[tuple] = None
    ) -> dict:
        """
        Handles API requests with error handling and logging.
        """
        try:
            response = requests.request(
                method, url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            response_json = response.json()
            
            if cache_key:
                self._request_cache[cache_key] = (payload, response_json)
                
            return response_json
            
        except HTTPError as e:
            # Pass self._logger explicitly
            return SDXValidator.handle_http_error(self._logger, e, operation)
        except Timeout:
            return {"status_code": 408,
                    "error_message": "Request Timeout",
                    "error_details": "The request timed out."
                   }
        except RequestException as e:
            return {"status_code": 500,
                    "error_message": "Request Error",
                    "error_details": str(e)
                   }

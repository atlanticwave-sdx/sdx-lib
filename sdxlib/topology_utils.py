# sdx_topology_utils.py
import re
from collections import defaultdict
from typing import Dict, List, Optional, Any, Union

import pandas as pd

from sdxlib.config import BASE_URL, VERSION
from sdxlib.exception import SDXException
from sdxlib.response import SDXResponse
from sdxlib.validator import SDXValidator
from sdxlib.request import _make_request

def get_topology(url_env: str = "test") -> dict:
    """
    Retrieves the topology from the SDX Controller.
    Returns a dict. On error, returns {"response": <payload>, "status_code": <code>}.
    """
    base_url = SDXValidator.validate_required_url(BASE_URL, url_env)
    url = f"{base_url}/topology"

    response, status_code = _make_request("GET", url, operation="get topology")
    if status_code != 200:
        return {"response": response, "status_code": status_code}

    return response or {}

def get_all_l2vpns(
        url_env: str = "test",
        archived: bool = False, 
        format: str = "dataframe",
        search: Optional[str] = None
    ) -> Union[pd.DataFrame, Dict[str, SDXResponse]]:
    """
    Retrieves all L2VPNs, optionally filtered by service_id or name.
    - format="raw": returns the raw dict from the controller: {service_id: {...}, ...}
    - format="json": returns a list[dict] with friendly fields for UI/logging
    - format="dataframe": returns a pandas DataFrame built from the friendly list
    """
    base_url = SDXValidator.validate_required_url(BASE_URL, url_env)
    url = f"{base_url}/l2vpn/{VERSION}/archived" if archived else f"{base_url}/l2vpn/{VERSION}"

    response, status = _make_request("GET", url, operation="retrieve all L2VPNs")
    if status != 200 or not isinstance(response, dict):
        # Normalize empties
        if format == "dataframe":
            return pd.DataFrame()
        return {} if format == "raw" else []
        
    # Convert JSON response to SDXResponse objects
    l2vpns = {
        service_id: SDXResponse(
            l2vpn_data
        ) for service_id, l2vpn_data in response.items()
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
            "endpoints": [
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

def _get_vlan_range(port, vlans_in_use: Dict[str, List[int]]) -> str:
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
        print(f"Error extracting VLAN range from port {port_id}: {e}")
        return "None"

def _format_port(port: Dict[str, Any], vlan_usage: Dict[str, List[int]]) -> Dict[str, str]:
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
        "VLANs Available": _get_vlan_range(port, vlan_usage),
        "VLANs in Use": "; ".join(map(str, vlan_usage.get(port_id, []))) or "None",
    }

def _parse_vlan_value(vlan_value: str) -> List[int]:
    """ Parses VLAN values from a string representation. """
    if ":" in vlan_value:
        try:
            start, end = map(int, vlan_value.split(":"))
            return list(range(start, end + 1))
        except ValueError:
            print(f"Invalid VLAN range: {vlan_value}")
    return [int(vlan_value)] if vlan_value.isdigit() else []

def _get_vlans_in_use(url_env: str = "test") -> Dict[str, List[int]]:
    """ Retrieves VLANs in use across all active L2VPNs. """
    vlan_usage = defaultdict(set)

    try:
        l2vpns = get_all_l2vpns(url_env, format="json")

        if not l2vpns:  # Handle None or empty case
            print("No L2VPN data retrieved.")
            return {}

        if isinstance(l2vpns, list):  # Convert list to dict for compatibility
            l2vpns = {vpn["Service ID"]: vpn for vpn in l2vpns}

        for l2vpn in l2vpns.values():
            for endpoint in l2vpn.get("endpoints", []):
                port_id, vlan = endpoint.get("port_id"), endpoint.get("vlan")
                if port_id and vlan: 
                    vlan_usage[port_id].update(_parse_vlan_value(vlan))
        return {port_id: sorted(vlans) for port_id, vlans in vlan_usage.items()}

    except SDXException as e:
        print(f"Error retrieving VLAN usage: {e}")
        return {}

def get_available_ports(url_env: str = "test", search: Optional[str] = None, format: str = "dataframe") -> Union[pd.DataFrame, List[dict]]:
    """
    Lists all available ports with unused VLANs.
    """
    topology = get_topology(url_env)
    used_vlans = _get_vlans_in_use(url_env)

    # Extract available ports from topology
    available_ports = []
    for node in topology.get("nodes", []):
        for port in node.get("ports", []):
            if port.get("status") == "up" and not port.get("nni"):
                    available_ports.append(_format_port(port, used_vlans))

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

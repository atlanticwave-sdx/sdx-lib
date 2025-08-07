# sdx_topology_utils.py

from typing import Dict, List, Optional, Any
import pandas as pd

from config import BASE_URL
from sdxlib.sdx_validator import SDXValidator
from sdxlib.sdx_request import _make_request, _get_headers


def get_topology(url_env: str = "test") -> dict:
    """
    Retrieves the topology from the SDX Controller.
    """
    base_url = SDXValidator.validate_required_url(BASE_URL, url_env)
    url = f"{base_url}topology"
    headers = {"Content-Type": "application/json"}

    response, status_code = _make_request("GET", url, headers, operation="get topology")
    if status_code != 200:
        return {}

    return response


def _get_vlans_in_use(topology: dict) -> Dict[str, List[int]]:
    """
    Parses the topology JSON to extract VLANs in use per port.
    """
    in_use = {}
    for service in topology.get("services", []):
        if service.get("type") != "l2vpn":
            continue
        for ep in service.get("endpoints", []):
            port_id = ep.get("port_id")
            vlan = ep.get("vlan")
            if port_id and isinstance(vlan, int):
                in_use.setdefault(port_id, []).append(vlan)
    return in_use


def _get_vlan_range(port: dict) -> List[int]:
    """
    Extracts the allowed VLAN range for a port.
    """
    vlan_range = port.get("vlan_range", "")
    if not vlan_range:
        return list(range(1, 4095))

    allowed = set()
    for part in vlan_range.split(","):
        if "-" in part:
            start, end = part.split("-")
            allowed.update(range(int(start), int(end) + 1))
        else:
            allowed.add(int(part))
    return sorted(allowed)


def _format_port(port: dict) -> str:
    """
    Generates a formatted label for a port.
    """
    return f"{port.get('name')} ({port.get('port_id')})"


def get_available_ports(url_env: str = "test", search: Optional[str] = None, format: str = "dataframe") -> Union[pd.DataFrame, List[dict]]:
    """
    Lists all available ports with unused VLANs.
    """
    topology = get_topology(url_env)
    ports = topology.get("ports", [])
    used_vlans = _get_vlans_in_use(topology)

    available = []

    for port in ports:
        port_id = port.get("port_id")
        vlan_range = _get_vlan_range(port)
        in_use = used_vlans.get(port_id, [])
        free_vlans = sorted(set(vlan_range) - set(in_use))

        label = _format_port(port)
        if search and search.lower() not in label.lower():
            continue

        available.append({
            "Port ID": port_id,
            "Name": port.get("name"),
            "Domain": port.get("domain"),
            "Node": port.get("node"),
            "Free VLANs": free_vlans[:10],
        })

    return pd.DataFrame(available) if format == "dataframe" else available


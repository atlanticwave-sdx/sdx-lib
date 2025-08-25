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


def get_topology(url_env: str = "test", source: str = "fabric") -> dict:
    """
    Retrieves the topology from the SDX Controller.
    On error: {"response": <payload>, "status_code": <code>}
    On success: raw topology dict.
    """
    base_url = SDXValidator.validate_required_url(BASE_URL, url_env)
    url = f"{base_url}/topology"

    response, status_code = _make_request(
            "GET", 
            url, 
            source = "fabric", 
            payload = None, 
            operation = "get topology")
    if status_code != 200:
        return {"response": response, "status_code": status_code}

    return response or {}


def get_all_l2vpns(
        url_env = "test",
        source = "fabric",
        archived: bool = False,
        format = "dataframe",   # "raw" | "json" | "dataframe"
        search: Optional[str] = None
    ) -> Union[pd.DataFrame, Dict[str, SDXResponse], List[dict]]:
    """
    Retrieves all L2VPNs.
    - format="raw": {service_id: SDXResponse, ...}
    - format="json": list[dict] friendly for UI/logging
    - format="dataframe": pandas.DataFrame from friendly list
    """
    base_url = SDXValidator.validate_required_url(BASE_URL, url_env)
    url = f"{base_url}/l2vpn/{VERSION}/archived" if archived else f"{base_url}/l2vpn/{VERSION}"

    response, status = _make_request(
            "GET", 
            url, 
            source = "fabric", 
            payload = None, 
            operation = "retrieve all L2VPNs")
    if status != 200 or not isinstance(response, dict):
        # Normalize empties by requested format
        if format == "raw":
            return {}
        if format == "json":
            return []
        return pd.DataFrame()

    # Convert JSON response to SDXResponse objects
    l2vpns: Dict[str, SDXResponse] = {
        service_id: SDXResponse(l2vpn_data)
        for service_id, l2vpn_data in response.items()
    }

    # Optional search filter
    if search:
        s = search.lower()
        l2vpns = {
            sid: l2vpn for sid, l2vpn in l2vpns.items()
            if s in sid.lower() or s in (l2vpn.name or "").lower()
        }

    if not l2vpns:
        if format == "raw":
            return {}
        if format == "json":
            return []
        return pd.DataFrame()

    if format == "raw":
        return l2vpns

    # Friendly list for JSON/DataFrame
    formatted: List[dict] = []
    for sid, l2vpn in l2vpns.items():
        eps = []
        for endpoint in (l2vpn.endpoints or []):
            if isinstance(endpoint, dict):
                eps.append({
                    "port_id": endpoint.get("port_id", "Unknown"),
                    "vlan": endpoint.get("vlan", "Unknown"),
                })
        formatted.append({
            "Service ID": sid,
            "Name": l2vpn.name,
            "endpoints": eps,
            "Ownership": getattr(l2vpn, "ownership", None),
            "Notifications": ", ".join(
                (e.get("email") if isinstance(e, dict) else str(e))
                for e in (l2vpn.notifications or [])
            ) if getattr(l2vpn, "notifications", None) else "None",
            "Scheduling": str(getattr(l2vpn, "scheduling", None) or "None"),
            "QoS Metrics": str(getattr(l2vpn, "qos_metrics", None) or "None"),
        })

    if format == "dataframe":
        return pd.DataFrame(formatted)
    return formatted  # "json"


def _parse_vlan_value(v: Any) -> List[int]:
    """
    Accepts:
      - int
      - "100"
      - "100-200" or "100:200"
      - "100,102,104-106"
    Returns a list of ints (expanded).
    """
    if isinstance(v, int):
        return [v]
    if not isinstance(v, str):
        return []

    parts = [p.strip() for p in v.split(",")]
    out: List[int] = []
    for part in parts:
        if "-" in part or ":" in part:
            sep = "-" if "-" in part else ":"
            try:
                start, end = map(int, part.split(sep))
                if start <= end:
                    out.extend(range(start, end + 1))
            except ValueError:
                print(f"Invalid VLAN range: {part}")
        else:
            if part.isdigit():
                out.append(int(part))
            else:
                print(f"Invalid VLAN value: {part}")
    return out


def _get_vlan_range(port: Dict[str, Any], vlans_in_use: Dict[str, List[int]]) -> str:
    """Compute available VLAN ranges on a port (excluding vlans_in_use)."""
    try:
        port_id = port.get("id", "Unknown")
        services = port.get("services", {}) or {}
        vlan_data = services.get("l2vpn-ptp", {}).get("vlan_range", [])
        in_use = set(vlans_in_use.get(port_id, []))

        if not (vlan_data and all(isinstance(v, list) and len(v) == 2 for v in vlan_data)):
            return "None"

        available = sorted(
            set(v for start, end in vlan_data for v in range(int(start), int(end) + 1)) - in_use
        )
        if not available:
            return "None"

        # Collapse into "a-b, c, d-e"
        ranges: List[str] = []
        start = end = available[0]
        for vlan in available[1:]:
            if vlan == end + 1:
                end = vlan
            else:
                ranges.append(f"{start}-{end}" if start != end else str(start))
                start = end = vlan
        ranges.append(f"{start}-{end}" if start != end else str(start))
        return ", ".join(ranges)

    except Exception as e:
        print(f"Error extracting VLAN range from port {port.get('id', 'Unknown')}: {e}")
        return "None"


def _format_port(port: Dict[str, Any], vlan_usage: Dict[str, List[int]]) -> Dict[str, str]:
    """Formats a port row for output."""
    port_id = port.get("id", "Unknown")

    # Parse URN: urn:sdx:port:<domain>:<device>:<port>
    domain = device = port_number = "Unknown"
    m = re.match(r"urn:sdx:port:(.*?):(.*?):(.*?)$", port_id or "")
    if m:
        domain, device, port_number = m.groups()

    entities = port.get("entities") or []
    entities_str = ", ".join(str(e) for e in entities)

    return {
        "Domain": domain,
        "Device": device,
        "Port": port_number,
        "Status": port.get("status", "Unknown"),
        "Port ID": port_id,
        "Entities": entities_str,
        "VLANs Available": _get_vlan_range(port, vlan_usage),
        "VLANs in Use": ", ".join(map(str, vlan_usage.get(port_id, []))) or "None",
    }


def _get_vlans_in_use(url_env: str = "test") -> Dict[str, List[int]]:
    """Aggregates VLANs in use across all active L2VPNs."""
    usage: Dict[str, set] = defaultdict(set)
    try:
        l2vpns = get_all_l2vpns(url_env, format="json")
        if not l2vpns:
            return {}

        # l2vpns is a list of friendly dicts
        for vpn in l2vpns:
            for ep in vpn.get("endpoints", []) or []:
                if not isinstance(ep, dict):
                    continue
                port_id = ep.get("port_id")
                vlan = ep.get("vlan")
                if port_id and vlan is not None:
                    for n in _parse_vlan_value(vlan):
                        usage[port_id].add(n)

        return {k: sorted(v) for k, v in usage.items()}
    except SDXException as e:
        print(f"Error retrieving VLAN usage: {e}")
        return {}


def get_available_ports(
        url_env = "test",
        source = "fabric",
        search: Optional[str] = None,
        format = "dataframe",  # "dataframe" | "json" | "print"
    ) -> Union[pd.DataFrame, List[dict], None]:
    """
    Lists all customer-facing ports (status=up and not NNI) with VLAN availability.
    """
    topology = get_topology(url_env)

    # Bubble up topology errors
    if isinstance(topology, dict) and topology.get("status_code"):
        if format == "print":
            print(f"Topology error: {topology.get('status_code')} {topology.get('response')}")
            return None
        return pd.DataFrame() if format == "dataframe" else []

    used_vlans = _get_vlans_in_use(url_env)

    # Gather ports
    available_ports: List[dict] = []
    for node in (topology.get("nodes", []) or []):
        for port in (node.get("ports", []) or []):
            try:
                if port.get("status") == "up" and not port.get("nni"):
                    available_ports.append(_format_port(port, used_vlans))
            except Exception:
                continue

    # Optional search filter
    if search:
        s = search.lower()
        available_ports = [
            p for p in available_ports
            if s in (p.get("Entities") or "").lower()
            or s in (p.get("Device") or "").lower()
            or s in (p.get("Port ID") or "").lower()
        ]

    if format == "print":
        if not available_ports:
            print(f"No ports found matching search term: '{search}'" if search else "No ports found.")
            return None

        headers = ["Domain", "Device", "Port", "Status", "Port ID", "Entities"]
        col_widths = [12, 12, 10, 8, 50, 50]
        header_row = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
        sep = "-" * len(header_row)
        print(header_row)
        print(sep)
        for p in available_ports:
            print(" | ".join(f"{str(p.get(field,'')):<{col_widths[i]}}" for i, field in enumerate(headers)))
        return None

    if format == "dataframe":
        return pd.DataFrame(available_ports)

    return available_ports  # "json"


# sdx_topology_utils.py
"""
Public API (external methods):
  - get_topology(token: str) -> dict
  - get_all_l2vpns(token: str, archived: bool = False, search: str | None = None)
  - get_available_ports(token: str, search: str | None = None)
  - get_port_vlans_available(token: str, port_id: str) -> dict | None
  - get_all_vlans_available(token: str) -> list[dict]
All other helpers are private (_prefixed).
"""
import re
from collections import defaultdict
from typing import Dict, List, Optional, Any

from sdxlib.config import BASE_URL, VERSION
from sdxlib.exception import SDXException
from sdxlib.response import normalize_l2vpn_response
from sdxlib.request import _make_request


def get_topology(token: str) -> Dict[str, Any]:
    """
    Fetch topology via NGINX (/production):
      - GET {BASE_URL}/topology with the Bearer token (validated by Lua)
      - On success: return the RAW topology dict (if API wraps, unwrap 'data')
      - On error:   return {"response": <payload>, "status_code": <code>}
    """
    if not token:
        raise ValueError("Bearer token is required for get_topology")

    topology_url = f"{BASE_URL}/topology"
    extra_headers = {"Authorization": f"Bearer {token}"}

    response_body, status_code = _make_request(
        method="GET",
        url=topology_url,
        payload=None,
        operation="get topology",
        extra_headers=extra_headers,
        timeout=60,
    )

    if status_code != 200:
        return {"response": response_body, "status_code": status_code}

    # Unwrap if the controller returns a list or wraps under {"data": ...}
    if isinstance(response_body, dict) and "data" in response_body and isinstance(response_body["data"], (dict, list)):
        return response_body["data"]

    return response_body or {}


def get_all_l2vpns(
        token: str,
        archived: bool = False,
        search: Optional[str] = None
    ) -> List[dict]:
    """
    Retrieves all L2VPNs.
    """
    if not token:
        raise ValueError("Bearer token is required for get_all_l2vpns")

    url = f"{BASE_URL}/l2vpn/{VERSION}/archived" if archived else f"{BASE_URL}/l2vpn/{VERSION}"
    extra_headers = {"Authorization": f"Bearer {token}"}

    response, status = _make_request(
            method="GET", 
            url=url, 
            payload = None, 
            operation = "retrieve all L2VPNs",
            extra_headers=extra_headers,
            timeout=60,
        )
    if status != 200 or not isinstance(response, dict):
        return []

    # Normalize into dicts keyed by service_id
    l2vpns: Dict[str, Dict[str, Any]] = {
            service_id: normalize_l2vpn_response(l2vpn_data)
            for service_id, l2vpn_data in response.items()
        }

    # Optional search filter
    if search:
        n_search = search.lower()
        l2vpns = {
            sid: l2vpn for sid, l2vpn in l2vpns.items()
            if n_search in sid.lower() or n_search in (l2vpn.get("name") or "").lower()
        }

    if not l2vpns:
        return []

    # Friendly list for JSON/DataFrame
    formatted: List[dict] = []
    for service_id, l2vpn in l2vpns.items():
        endpoints_list = []
        for endpoint in (l2vpn.get("endpoints") or []):
            if isinstance(endpoint, dict):
                endpoints_list.append({
                    "port_id": endpoint.get("port_id", "Unknown"),
                    "vlan": endpoint.get("vlan", "Unknown"),
                })
        formatted.append({
            "Service ID": service_id,
            "Name": l2vpn.get("name"),
            "endpoints": endpoints_list,
            "Ownership": l2vpn.get("ownership"),
            "Notifications": ", ".join(
                (email.get("email") if isinstance(email, dict) else str(email))
                for email in (l2vpn.get("notifications") or [])
            ) if l2vpn.get("notifications") else "None",
            "Scheduling": str(l2vpn.get("scheduling") or "None"),
            "QoS Metrics": str(l2vpn.get("qos_metrics") or "None"),
        })

    return formatted  # "json"


def _parse_vlan_value(vlan_val: Any) -> List[int]:
    """
    Accepts:
      - int
      - "100"
      - "100-200" or "100:200"
      - "100,102,104-106"
    Returns a list of ints (expanded).
    """
    if isinstance(vlan_val, int):
        return [vlan_val]
    if not isinstance(vlan_val, str):
        return []

    parts = [part_split.strip() for part_split in vlan_val.split(",")]
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


# --- helpers for advertised ranges (strings or [start,end]) ---

def _iter_advertised_vlan_ints(raw_ranges: Any) -> List[int]:
    """
    Normalize and expand controller-advertised VLAN ranges into a list of ints.
    Accepts:
      - [[start, end], ...]  (canonical)
      - ["start-end", ...] or ["start:end", ...]  (string form)
    """
    if not raw_ranges:
        return []
    expanded: List[int] = []
    for item in raw_ranges:
        # canonical pair
        if isinstance(item, list) and len(item) == 2:
            try:
                a, b = int(item[0]), int(item[1])
            except Exception:
                continue
            if a <= b:
                expanded.extend(range(a, b + 1))
            continue
        # "a-b" or "a:b"
        if isinstance(item, str):
            text = item.strip().replace(" ", "")
            sep = "-" if "-" in text else (":" if ":" in text else None)
            if not sep:
                continue
            try:
                a, b = map(int, text.split(sep))
            except Exception:
                continue
            if a <= b:
                expanded.extend(range(a, b + 1))
            continue
    return expanded


def _collapse_ints_to_ranges(values: List[int]) -> str:
    """Collapse sorted ints into 'a-b, c, d-e' string (or 'None' if empty)."""
    if not values:
        return "None"
    values = sorted(set(values))
    out: List[str] = []
    start = end = values[0]
    for v in values[1:]:
        if v == end + 1:
            end = v
        else:
            out.append(f"{start}-{end}" if start != end else str(start))
            start = end = v
    out.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(out)


def _get_vlan_range(port: Dict[str, Any], vlans_in_use: Dict[str, List[int]]) -> str:
    """Compute available VLAN ranges on a port (excluding vlans_in_use)."""
    try:
        port_id = port.get("id", "Unknown")
        services = port.get("services", {}) or {}

        # accept both hyphen and underscore keys
        svc = services.get("l2vpn-ptp") or services.get("l2vpn_ptp") or {}
        raw_ranges = svc.get("vlan_range", [])

        advertised = _iter_advertised_vlan_ints(raw_ranges)
        if not advertised:
            return "None"

        in_use = set(vlans_in_use.get(port_id, []))
        available = sorted(set(advertised) - in_use)
        return _collapse_ints_to_ranges(available)

    except Exception as e:
        print(f"Error extracting VLAN range from port {port.get('id', 'Unknown')}: {e}")
        return "None"


def _format_port(port: Dict[str, Any], vlan_usage: Dict[str, List[int]]) -> Dict[str, str]:
    """Formats a port row for output."""
    port_id = port.get("id", "Unknown")

    # Parse URN: urn:sdx:port:<domain>:<device>:<port>
    domain = device = port_number = "Unknown"
    match = re.match(r"urn:sdx:port:(.*?):(.*?):(.*?)$", port_id or "")
    if match:
        domain, device, port_number = match.groups()

    entities = port.get("entities") or []
    entities_str = ", ".join(str(entity) for entity in entities)

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


def _get_vlans_in_use(token: str) -> Dict[str, List[int]]:
    """Aggregates VLANs in use across all active L2VPNs."""
    usage: Dict[str, set] = defaultdict(set)
    try:
        l2vpns = get_all_l2vpns(token=token)
        if not l2vpns:
            return {}

        # l2vpns is a list of friendly dicts
        for l2vpn_entry in l2vpns:
            for endpoint in l2vpn_entry.get("endpoints", []) or []:
                if not isinstance(endpoint, dict):
                    continue
                port_id = endpoint.get("port_id")
                vlan = endpoint.get("vlan")
                if port_id and vlan is not None:
                    for vlan_number in _parse_vlan_value(vlan):
                        usage[port_id].add(vlan_number)

        return {key: sorted(value) for key, value in usage.items()}
    except SDXException as e:
        print(f"Error retrieving VLAN usage: {e}")
        return {}

# ---- helpers (top-level, no nested defs) ----

def _has_non_empty_values(row: dict, columns: List[str]) -> bool:
    """Return True only if every listed column has a real (non-empty/None/'None') value."""
    for column_name in columns:
        value = row.get(column_name)
        if value is None:
            return False
        if isinstance(value, str) and value.strip().lower() in ("", "none"):
            return False
    return True


def _parse_search_tokens(search: str) -> tuple[List[tuple[str, str]], List[str]]:
    """Split search into key:value tokens and plain terms."""
    key_value_terms: List[tuple[str, str]] = []
    plain_terms: List[str] = []
    for token in (t for t in search.split() if t):
        if ":" in token:
            key, value = token.split(":", 1)
            key_value_terms.append((key.strip().lower(), value.strip()))
        else:
            plain_terms.append(token.lower())
    return key_value_terms, plain_terms


def _row_matches_search(
    row: dict,
    key_value_terms: List[tuple[str, str]],
    plain_terms: List[str],
    field_map: Dict[str, str],
) -> bool:
    """Check if a row satisfies key:value filters and plain-term search."""
    # key:value filters
    for key, value in key_value_terms:
        column_name = field_map.get(key, key)
        column_text = str(row.get(column_name, "")).lower()
        if value == "":  # keep only rows where this field is non-empty
            if not _has_non_empty_values(row, [column_name]):
                return False
        else:
            if value.lower() not in column_text:
                return False

    # plain terms across common columns
    if plain_terms:
        haystacks = (
            str(row.get("Entities", "")).lower(),
            str(row.get("Device", "")).lower(),
            str(row.get("Port ID", "")).lower(),
        )
        for term in plain_terms:
            if not any(term in text for text in haystacks):
                return False

    return True


# ---- main function (single-pass combined filtering + projection) ----

def get_available_ports(
        token: str,
        search: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[dict]:
    """
    Lists all customer-facing ports (status=up and not NNI) with VLAN availability.
    Applies, in a single pass:
      - non-empty check for any requested 'fields'
      - search filtering (plain terms and key:value tokens)
      - projection to requested 'fields' (if provided)
    """
    if not token:
        raise ValueError("Bearer token is required for get_available_ports")

    topology = get_topology(token=token)
    if isinstance(topology, dict) and topology.get("status_code"):
        return []

    vlans_in_use = _get_vlans_in_use(token=token)

    # Build candidate rows
    candidate_rows: List[dict] = []
    for node in (topology.get("nodes", []) or []):
        for port in (node.get("ports", []) or []):
            try:
                if port.get("status") == "up" and not port.get("nni"):
                    candidate_rows.append(_format_port(port, vlans_in_use))
            except Exception:
                continue

    # Prepare combined filtering inputs
    selected_fields = [name.strip() for name in (fields or []) if name and name.strip()]

    search_field_map = {
        "entities": "Entities",
        "device": "Device",
        "port": "Port",
        "port_id": "Port ID",
        "status": "Status",
        "vlan": "VLANs Available",
        "vlan_available": "VLANs Available",
        "vlan_in_use": "VLANs in Use",
    }

    key_value_terms: List[tuple[str, str]] = []
    plain_terms: List[str] = []
    if search:
        key_value_terms, plain_terms = _parse_search_tokens(search)

    # Single-pass filter + project
    filtered_rows: List[dict] = []
    for row in candidate_rows:
        if selected_fields and not _has_non_empty_values(row, selected_fields):
            continue
        if search and not _row_matches_search(row, key_value_terms, plain_terms, search_field_map):
            continue
        filtered_rows.append(
            {column_name: row.get(column_name) for column_name in selected_fields}
            if selected_fields else row
        )

    return filtered_rows


def get_device_info(
    token: str,
    device: str,
    port_id: Optional[str] = None,
    fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
    """
    Return device metadata and its ports (formatted like available_ports).
    fields: optional projection list for each port dict.
    """
    if not token:
        raise ValueError("Bearer token is required for get_device_info")
    if not device or not isinstance(device, str):
        raise ValueError("device must be a non-empty string")

    topology = get_topology(token=token)
    if isinstance(topology, dict) and topology.get("status_code"):
        return {"device": None, "columns": [], "ports": []}

    vlan_usage = _get_vlans_in_use(token=token)

    matched_node = None
    for node in (topology.get("nodes", []) or []):
        node_name = node.get("name") or ""
        node_id = node.get("id") or ""
        if device in {node_name, node_id}:
            matched_node = node
            break
        for port in (node.get("ports", []) or []):
            urn = (port.get("id") or "")
            match = re.match(r"urn:sdx:port:(.*?):(.*?):(.*?)$", urn)
            if match and match.groups()[1] == device:
                matched_node = node
                break
        if matched_node:
            break

    if not matched_node:
        return {"device": None, "columns": [], "ports": []}

    port_rows: List[dict] = []
    for port in (matched_node.get("ports", []) or []):
        try:
            formatted = _format_port(port, vlan_usage)
            if port_id and formatted.get("Port ID") != port_id:
                continue
            port_rows.append(formatted)
        except Exception:
            continue

    selected_fields = [name.strip() for name in (fields or []) if name and name.strip()]
    if selected_fields:
        port_rows = [
            {column_name: row.get(column_name) for column_name in selected_fields}
            for row in port_rows
        ]

    columns = selected_fields or [
        "Domain", "Device", "Port", "Status", "Port ID", "Entities", "VLANs Available", "VLANs in Use"
    ]

    device_meta = {
        "name": matched_node.get("name"),
        "id": matched_node.get("id"),
        "status": matched_node.get("status"),
        "domain": port_rows[0].get("Domain") if port_rows else None,
    }

    return {"device": device_meta, "columns": columns, "ports": port_rows}


# ---- NEW: VLAN availability helpers ----

def _normalize_vlan_list_string(ranges_text: str) -> List[str]:
    """
    Convert a human string like '100-120, 200, 300-305' → ['100-120','200','300-305'].
    Returns [] for None/empty/'None'.
    """
    if not isinstance(ranges_text, str):
        return []
    text = ranges_text.strip()
    if not text or text.lower() == "none":
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def get_port_vlans_available(token: str, port_id: str) -> Optional[Dict[str, Any]]:
    """
    Return VLAN availability (as compact ranges) for a single port URN.
    Uses the same availability computation as get_available_ports:
      - derives 'vlan_range' from topology
      - subtracts VLANs currently in use by active L2VPNs
    Output:
      {"port_id": "<urn>", "vlans_available": ["100-200","300",...]}  or  None if not found
    """
    if not token:
        raise ValueError("Bearer token is required for get_port_vlans_available")
    if not port_id or not isinstance(port_id, str):
        raise ValueError("port_id must be a non-empty string")

    topology = get_topology(token=token)
    if isinstance(topology, dict) and topology.get("status_code"):
        return None

    vlan_usage = _get_vlans_in_use(token=token)

    target_port: Optional[Dict[str, Any]] = None
    for node in (topology.get("nodes", []) or []):
        for port in (node.get("ports", []) or []):
            if str(port.get("id") or "") == port_id:
                target_port = port
                break
        if target_port:
            break

    if not target_port:
        return None

    ranges_text = _get_vlan_range(target_port, vlan_usage)  # 'a-b, c, d-e' or 'None'
    return {
        "port_id": port_id,
        "vlans_available": _normalize_vlan_list_string(ranges_text),
    }


def get_all_vlans_available(token: str) -> List[Dict[str, Any]]:
    """
    Return VLAN availability for all ports as a list of:
      {"port_id": "<urn>", "vlans_available": ["100-200","300",...]}
    Uses the same logic as get_available_ports (subtract in-use VLANs).
    """
    if not token:
        raise ValueError("Bearer token is required for get_all_vlans_available")

    topology = get_topology(token=token)
    if isinstance(topology, dict) and topology.get("status_code"):
        return []

    vlan_usage = _get_vlans_in_use(token=token)

    results: List[Dict[str, Any]] = []
    for node in (topology.get("nodes", []) or []):
        for port in (node.get("ports", []) or []):
            try:
                port_urn = str(port.get("id") or "")
                if not port_urn:
                    continue
                ranges_text = _get_vlan_range(port, vlan_usage)
                results.append({
                    "port_id": port_urn,
                    "vlans_available": _normalize_vlan_list_string(ranges_text),
                })
            except Exception:
                continue

    return results


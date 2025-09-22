# sdxlib/validator.py
"""
Lightweight, function-only validators used by sdxlib.l2vpn and callers.

- No TokenAuth dependency
- No sessions/DB lookups
- Pure input validation & error-shaping utilities
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from requests.exceptions import HTTPError

# ---------- basic constants ----------

PORT_ID_PATTERN = r"^urn:sdx:port:[a-zA-Z0-9.,-_/]+:[a-zA-Z0-9.,-_/]+:[a-zA-Z0-9.,-_/]+$"
ALLOWED_SPECIAL_VLANS = {"any", "all", "untagged"}

# ---------- simple URL/name checks ----------

def validate_required_url(base_url: str) -> str:
    """Return base_url if it looks non-empty; raise otherwise."""
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("BASE_URL must be a non-empty string.")
    return base_url

def validate_required_attributes(base_url: str, name: Optional[str], endpoints: Optional[List[Dict[str, str]]]) -> None:
    """Ensure minimal required fields before calling the controller."""
    validate_required_url(base_url)
    validate_name(name)
    validate_endpoints(endpoints)

def validate_name(name: Optional[str]) -> str:
    """Non-empty <= 50 chars."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string.")
    if len(name) > 50:
        raise ValueError("name must be at most 50 characters.")
    return name

# ---------- email / notifications ----------

def is_valid_email(email: Any) -> bool:
    return isinstance(email, str) and re.match(r"^\S+@\S+$", email) is not None

def validate_notifications(notifications: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
    """List of {'email': 'user@example.org'} with size <= 10."""
    if notifications is None:
        return None
    if not isinstance(notifications, list):
        raise ValueError("notifications must be a list of objects with 'email'.")
    if len(notifications) > 10:
        raise ValueError("notifications can contain at most 10 entries.")
    validated: List[Dict[str, str]] = []
    for item in notifications:
        if not isinstance(item, dict) or "email" not in item:
            raise ValueError("each notification must be a dict with an 'email' key.")
        if not is_valid_email(item["email"]):
            raise ValueError(f"invalid email format: {item['email']}")
        validated.append({"email": item["email"]})
    return validated

# ---------- VLAN / endpoint validation ----------

def _validate_vlan_range(text: str) -> str:
    """Accept 'A:B' where 1 <= A < B <= 4095."""
    try:
        left, right = map(int, text.split(":"))
    except Exception:
        raise ValueError(
            f"invalid VLAN range '{text}'; expected 'A:B' with integers."
        )
    if not (1 <= left < right <= 4095):
        raise ValueError("VLAN range values must satisfy 1 <= A < B <= 4095.")
    return text

def _validate_endpoint_dict(endpoint: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(endpoint, dict):
        raise TypeError("endpoint must be a dict.")
    port_id = endpoint.get("port_id")
    vlan = endpoint.get("vlan")
    if not isinstance(port_id, str) or not re.match(PORT_ID_PATTERN, port_id):
        raise ValueError(f"invalid port_id format: {port_id}")
    if not isinstance(vlan, str) or not vlan.strip():
        raise ValueError("endpoint requires 'vlan' as non-empty string.")

    v = vlan.strip().lower()
    if v in ALLOWED_SPECIAL_VLANS:
        return {"port_id": port_id, "vlan": v}

    if v.isdigit():
        vid = int(v)
        if 1 <= vid <= 4095:
            return {"port_id": port_id, "vlan": v}
        raise ValueError("VLAN must be between 1 and 4095.")

    if ":" in v:
        return {"port_id": port_id, "vlan": _validate_vlan_range(v)}

    raise ValueError(
        "vlan must be 'any'|'all'|'untagged', a number (1..4095), or a range 'A:B'."
    )

def validate_endpoints(endpoints: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """
    - list with >= 2 entries
    - all share a single VLAN semantics rule:
      * if any endpoint uses a range -> all must use EXACTLY that same range
      * if any uses special -> all must use the same special keyword
      * otherwise single numeric VLAN -> all must use that same number
    """
    if not isinstance(endpoints, list) or len(endpoints) < 2:
        raise ValueError("endpoints must be a list with at least 2 entries.")

    validated = [_validate_endpoint_dict(ep) for ep in endpoints]
    vlans = {ep["vlan"] for ep in validated}

    # special cases must be uniform
    if any(v in ALLOWED_SPECIAL_VLANS for v in vlans):
        if len(vlans) != 1:
            raise ValueError("when using 'any'|'all'|'untagged', all endpoints must use the same value.")
        return validated

    # range case must be uniform
    if any(":" in v for v in vlans):
        if len(vlans) != 1:
            raise ValueError("when using VLAN ranges, all endpoints must share the same range.")
        return validated

    # numeric case must be uniform
    if not all(v.isdigit() for v in vlans):
        raise ValueError("mixed VLAN specification; use all numeric, all range, or the same special keyword.")
    if len(vlans) != 1:
        raise ValueError("all endpoints must use the same numeric VLAN.")
    return validated

# ---------- scheduling / QoS ----------

_ISO8601_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

def is_valid_iso8601(ts: str) -> bool:
    return isinstance(ts, str) and _ISO8601_Z.match(ts) is not None

def validate_scheduling(scheduling: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Expect {'start_time': ISO8601Z, 'end_time': ISO8601Z}."""
    if scheduling is None:
        return None
    if not isinstance(scheduling, dict):
        raise TypeError("scheduling must be a dict.")
    start = scheduling.get("start_time")
    end = scheduling.get("end_time")
    if start is not None and not is_valid_iso8601(start):
        raise ValueError("start_time must be ISO8601 (YYYY-MM-DDTHH:MM:SSZ).")
    if end is not None and not is_valid_iso8601(end):
        raise ValueError("end_time must be ISO8601 (YYYY-MM-DDTHH:MM:SSZ).")
    if start and end and end <= start:
        raise ValueError("end_time must be after start_time.")
    out: Dict[str, str] = {}
    if start: out["start_time"] = start
    if end:   out["end_time"] = end
    return out or None

def validate_qos_metrics(qos: Optional[Dict[str, Dict[str, Union[int, bool]]]]) -> Optional[Dict[str, Dict[str, Union[int, bool]]]]:
    """
    Accept keys in {'min_bw','max_delay','max_number_oxps'} with:
      - value: int in a reasonable range
      - strict: optional bool
    """
    if qos is None:
        return None
    if not isinstance(qos, dict):
        raise TypeError("qos_metrics must be a dict.")
    ranges = {"min_bw": (0, 100), "max_delay": (0, 1000), "max_number_oxps": (1, 100)}
    out: Dict[str, Dict[str, Union[int, bool]]] = {}
    for key, spec in qos.items():
        if key not in ranges or not isinstance(spec, dict):
            raise ValueError(f"invalid QoS metric: {key}")
        val = spec.get("value")
        strict = spec.get("strict")
        if not isinstance(val, int):
            raise ValueError(f"QoS '{key}.value' must be an int.")
        lo, hi = ranges[key]
        if not (lo <= val <= hi):
            raise ValueError(f"QoS '{key}.value' must be between {lo} and {hi}.")
        if "strict" in spec and not isinstance(strict, bool):
            raise ValueError(f"QoS '{key}.strict' must be a bool.")
        out[key] = {"value": val} if "strict" not in spec else {"value": val, "strict": strict}
    return out

# ---------- HTTP error shaping (optional helper) ----------

_METHOD_MESSAGES = {
    201: "L2VPN Service Created",
    400: "Invalid JSON or incomplete/incorrect body",
    401: "Not authorized",
    402: "Request not compatible",
    409: "L2VPN Service already exists",
    410: "Strict QoS requirements cannot be fulfilled",
    411: "Scheduling not possible",
    412: "No path available between endpoints",
    422: "Attribute not supported by SDX-LC/OXPO",
}

def map_http_error(logger: Optional[logging.Logger], exc: HTTPError, operation: str) -> Dict[str, Any]:
    """Convert HTTPError into a consistent dict."""
    if logger:
        logger.error("HTTP error during %s: %s", operation, exc)
    status = getattr(getattr(exc, "response", None), "status_code", None)
    ctype = getattr(getattr(exc, "response", None), "headers", {}).get("Content-Type", "")
    body = None
    try:
        if "application/json" in (ctype or ""):
            body = exc.response.json()
        else:
            body = exc.response.text
    except Exception:
        body = "unavailable"
    return {
        "status_code": status or 0,
        "message": _METHOD_MESSAGES.get(status, "Unknown error"),
        "operation": operation,
        "details": body,
    }


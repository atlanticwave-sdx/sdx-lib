# sdxlib/response.py
"""
Response normalization utilities for SDX library.

Contract:
- Callers SHOULD return a dict with keys: {"status_code", "data", "error"}.
- Success (2xx):   {"status_code": <int>, "data": <payload>, "error": None}
- Non-success:     {"status_code": <int>, "data": <payload>, "error": <short message>}

This module centralizes the shaping of both success and error responses so that
route wrappers (e.g., sdxlib/l2vpn.py) stay thin and never stringify large dicts
into the "error" field.
"""

from typing import Any, Dict, List, Optional


# ---------------------------
# Success shapers (domain-specific)
# ---------------------------

def normalize_l2vpn_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Project raw L2VPN dicts into a stable, consumer-friendly shape."""
    return {
        "service_id": data.get("service_id", "unknown"),
        "name": data.get("name", ""),
        "endpoints": data.get("endpoints", []),
        "ownership": data.get("ownership", ""),
        "creation_date": data.get("creation_date", ""),
        "archived_date": data.get("archived_date", ""),
        "status": data.get("status", ""),
        "state": data.get("state", ""),
        "counters_location": data.get("counters_location", ""),
        "last_modified": data.get("last_modified", ""),
        "current_path": data.get("current_path", []),
        "oxp_service_ids": data.get("oxp_service_ids", []),
        "description": data.get("description"),
        "notifications": data.get("notifications"),
        "scheduling": data.get("scheduling"),
        "qos_metrics": data.get("qos_metrics"),
    }


# ---------------------------
# Generic result shapers
# ---------------------------

def _derive_error_message(payload: Any, status_code: int, method: str) -> str:
    """
    Extract a concise message from a controller payload; fall back to a generic one.
    - If payload is dict, prefer common error keys.
    - If payload is text/other, truncate to a safe preview.
    """
    if isinstance(payload, dict):
        message = (
            payload.get("error")
            or payload.get("message")
            or payload.get("detail")
            or payload.get("title")
        )
        if message:
            return str(message)
        # If the server wrapped a non-JSON error inside a dict (our HTTP helper may do this)
        # try to surface a short 'body_sample' if present.
        body_sample = payload.get("body_sample")
        if isinstance(body_sample, str) and body_sample.strip():
            return body_sample.strip()[:500]
    # Fallback for non-dict bodies
    text_preview = (str(payload) if payload is not None else "").strip()
    if text_preview:
        return text_preview[:500]
    return f"{method} failed with status {status_code}"


def normalize_error_response(
    response_payload: Any,
    status_code: int,
    method: str = "operation",
) -> Dict[str, Any]:
    """
    Wrap a failed API response into a consistent dict with a concise error message.
    """
    error_message = _derive_error_message(response_payload, status_code, method)
    return {
        "status_code": status_code,
        "data": response_payload,
        "error": error_message,
    }


def normalize_result(
    response_payload: Any,
    status_code: int,
    method: str = "operation",
) -> Dict[str, Any]:
    """
    Return a normalized result dict for both success and error cases.
    - 2xx → error=None
    - otherwise → concise error message derived from payload
    """
    if 200 <= status_code < 300:
        return {"status_code": status_code, "data": response_payload, "error": None}
    return normalize_error_response(response_payload, status_code, method)


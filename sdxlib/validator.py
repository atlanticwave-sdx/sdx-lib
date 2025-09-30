# sdxlib/validator.py
"""
Slim validators and HTTP error shaping for sdxlib.

This module intentionally omits VLAN/endpoint validation logic.
Those rules now live in the client layer (sdxclient), which validates
request bodies before sending them to the controller.

Provided here:
- Basic input checks useful across routes (URL, name, notifications).
- Controller error shaping with friendly messages.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from requests.exceptions import HTTPError

# ---------- status → friendly message mapping ----------

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

# ---------- simple input checks (generic) ----------

def validate_required_url(base_url: str) -> str:
    """Return base_url if it looks non-empty; raise otherwise."""
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("BASE_URL must be a non-empty string.")
    return base_url


def validate_name(name: Optional[str]) -> str:
    """Non-empty name, max 50 chars."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string.")
    if len(name) > 50:
        raise ValueError("name must be at most 50 characters.")
    return name


_EMAIL_RE = re.compile(r"^\S+@\S+$")

def is_valid_email(email: Any) -> bool:
    return isinstance(email, str) and _EMAIL_RE.match(email) is not None


def validate_notifications(
    notifications: Optional[List[Dict[str, str]]]
) -> Optional[List[Dict[str, str]]]:
    """
    Accepts a list of {'email': 'user@example.org'} with size <= 10.
    Returns a normalized list or None if notifications is None.
    """
    if notifications is None:
        return None
    if not isinstance(notifications, list):
        raise ValueError("notifications must be a list of objects with 'email'.")
    if len(notifications) > 10:
        raise ValueError("notifications can contain at most 10 entries.")

    normalized: List[Dict[str, str]] = []
    for item in notifications:
        if not isinstance(item, dict) or "email" not in item:
            raise ValueError("each notification must be a dict with an 'email' key.")
        email_value = item["email"]
        if not is_valid_email(email_value):
            raise ValueError(f"invalid email format: {email_value}")
        normalized.append({"email": email_value})
    return normalized

# ---------- HTTP error shaping ----------

def map_http_error(
    logger: Optional[logging.Logger],
    exc: HTTPError,
    operation: str,
) -> Dict[str, Any]:
    """
    Convert requests.HTTPError into a consistent dict while preserving
    controller-provided details when available.
    """
    if logger:
        logger.error("HTTP error during %s: %s", operation, exc)

    status = getattr(getattr(exc, "response", None), "status_code", None)
    headers = getattr(getattr(exc, "response", None), "headers", {}) or {}
    ctype = headers.get("Content-Type", "") or ""

    details: Any
    try:
        if "application/json" in ctype.lower():
            details = exc.response.json()
        else:
            details = exc.response.text
    except Exception:
        details = "unavailable"

    return {
        "status_code": status or 0,
        "message": _METHOD_MESSAGES.get(status, "Unknown error"),
        "operation": operation,
        "details": details,
    }


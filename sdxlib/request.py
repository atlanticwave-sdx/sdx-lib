# sdx_request.py

import requests
from requests.exceptions import RequestException, HTTPError, Timeout
from typing import Tuple, Optional, Dict, Any

from sdxlib.token_auth import TokenAuth

JSON_SAMPLE_CHARS = 600  # how many chars of a non-JSON/HTML body to include on errors

def _make_request(
    method,
    url,
    source = "fabric",
    payload: Optional[dict] = None,
    operation = "",
    cache_key: Optional[Any] = None,   # kept for compatibility; not used here
    extra_headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
) -> Tuple[Dict[str, Any], int]:
    """
    Generic HTTP request helper for the SDX controller.
    Returns: (response_dict, status_code)

    - On success (2xx with JSON): returns parsed JSON dict (or list wrapped under {"data": ...})
    - On non-JSON or non-2xx: returns a structured error payload with helpful diagnostics
    """
    headers = _get_headers(source)
    if "error" in headers:
        # Token missing/unavailable
        return {
            "status_code": 401,
            "error": headers["error"],
            "operation": operation,
            "url": url,
        }, 401

    if extra_headers:
        headers.update(extra_headers)

    try:
        resp = requests.request(method, url, json=payload, headers=headers, timeout=timeout)
    except Timeout:
        return {
            "status_code": 408,
            "error": "Request timeout",
            "operation": operation,
            "url": url,
        }, 408
    except RequestException as e:
        return {
            "status_code": 0,
            "error": f"Request failed: {e}",
            "operation": operation,
            "url": url,
        }, 0

    status = resp.status_code
    ctype = (resp.headers.get("Content-Type") or "").lower()
    text = resp.text or ""

    # Try JSON parsing when content-type looks like JSON
    if "application/json" in ctype:
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            # JSON expected but failed to parse
            data = {
                "status_code": status,
                "error": f"JSON parse error: {e}",
                "content_type": ctype,
                "body_sample": text[:JSON_SAMPLE_CHARS],
                "operation": operation,
                "url": url,
            }
            return data, status

        # If success, return parsed JSON
        if 200 <= status < 300:
            # Ensure dict return type (wrap list)
            if isinstance(data, list):
                return {"data": data}, status
            return data or {}, status

        # Non-2xx with JSON body: pass it through but ensure status_code present
        if isinstance(data, dict):
            data.setdefault("status_code", status)
            data.setdefault("operation", operation)
            data.setdefault("url", url)
            return data, status
        else:
            # JSON array error body → wrap for consistency
            return {
                "status_code": status,
                "error": "Non-dict JSON error response",
                "data": data,
                "operation": operation,
                "url": url,
            }, status

    # Non-JSON response (e.g., HTML error page, empty body, text/plain)
    if 200 <= status < 300:
        # Unexpected: success but non-JSON body. Return as text.
        return {
            "status_code": status,
            "data": text[:JSON_SAMPLE_CHARS],
            "content_type": ctype,
            "warning": "Non-JSON success response",
            "operation": operation,
            "url": url,
        }, status

    # Error + non-JSON body
    return {
        "status_code": status,
        "error": "Non-JSON error response",
        "body_sample": text[:JSON_SAMPLE_CHARS],
        "content_type": ctype,
        "operation": operation,
        "url": url,
    }, status


def _get_headers(source: str = "fabric") -> Dict[str, str]:
    """
    Build authorization and default headers.
    Returns headers OR {"error": "..."} if token is missing/unavailable.
    """
    try:
        token = TokenAuth().load_token(source)
        if not token:
            return {"error": "Missing token (token not found)."}
    except Exception as e:
        return {"error": f"Could not load token: {e}"}

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

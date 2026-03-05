# sdxlib/request.py
"""
Request helper for SDX API.
Handles validation, user/service preflight, and HTTP calls.
"""

import requests
from requests.exceptions import RequestException, Timeout
from typing import Tuple, Dict, Any, Optional
import json

JSON_SAMPLE_CHARS = 600


def _make_request(
    method: str,
    url: str,
    payload: Optional[dict] = None,
    operation: str = "",
    extra_headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
) -> Tuple[Dict[str, Any], int]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    try:
        # ADDED verify=False to bypass the internal SSL 'bad certificate' error
        resp = requests.request(method, url, json=payload, headers=headers, timeout=timeout, verify=False)
    except Timeout:
        return {"status_code": 408, "error": "Request timeout", "operation": operation, "url": url}, 408
    except RequestException as e:
        # CHANGED 0 to 502 (Bad Gateway) to prevent Flask/curl from crashing!
        return {"status_code": 502, "error": str(e), "operation": operation, "url": url}, 502

    status = resp.status_code
    ctype = (resp.headers.get("Content-Type") or "").lower()
    text = resp.text or ""

    if "application/json" in ctype:
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"status_code": status, "error": f"JSON parse error: {e}", "body_sample": text[:JSON_SAMPLE_CHARS]}, status

        if 200 <= status < 300:
            return ({"data": data} if isinstance(data, list) else data or {}), status
        if isinstance(data, dict):
            data.setdefault("status_code", status)
            return data, status
        return {"status_code": status, "error": "Non-dict JSON error response", "data": data}, status

    if 200 <= status < 300:
        return {"status_code": status, "data": text[:JSON_SAMPLE_CHARS], "warning": "Non-JSON success"}, status

    return {"status_code": status, "error": "Non-JSON error response", "body_sample": text[:JSON_SAMPLE_CHARS]}, status


# sdx_request.py

import requests
from requests.exceptions import RequestException, HTTPError, Timeout
from typing import Optional, Dict, Any


def _make_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    payload: Optional[dict] = None,
    operation: str = "",
    cache_key: Optional[Any] = None,
) -> tuple:
    """
    Generic method for making HTTP requests to the SDX controller.
    Returns a tuple: (response dict, status code)
    """
    try:
        response = requests.request(method, url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        json_data = response.json()
        return json_data, response.status_code
    except HTTPError as e:
        error_response = {"status_code": e.response.status_code if e.response else 500, "error": str(e)}
        return error_response, error_response["status_code"]
    except Timeout:
        return {"status_code": 408, "error": "Timeout"}, 408
    except RequestException as e:
        return {"status_code": 500, "error": str(e)}, 500


def _get_headers(client) -> Dict[str, str]:
    """Build authorization headers for requests."""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {client.token_auth.fabric_token}",
    }


def _build_payload(client) -> dict:
    """Constructs a request payload from SDXClient instance variables."""
    return {
        key: value
        for key, value in {
            "name": client.name,
            "endpoints": client.endpoints,
            "ownership": client.ownership,
            "description": client.description,
            "notifications": client.notifications,
            "scheduling": client.scheduling,
            "qos_metrics": client.qos_metrics,
        }.items()
        if value is not None
    }


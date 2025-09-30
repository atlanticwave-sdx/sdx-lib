# sdxlib/l2vpn.py
from typing import Dict, Any, List
from sdxlib.request import _make_request
from sdxlib.config import BASE_URL
from sdxlib.response import normalize_result

VERSION = "1.0"

def create_l2vpn(token: str, name: str, endpoints: List[Dict[str, str]], **kwargs) -> dict:
    url = f"{BASE_URL}/l2vpn/{VERSION}"
    payload = {"name": name, "endpoints": endpoints, **kwargs}
    response, status = _make_request(
        "POST",
        url,
        payload=payload,
        extra_headers={"Authorization": f"Bearer {token}"},
        operation="create L2VPN",
    )
    return normalize_result(response, status, "create L2VPN")


def update_l2vpn(token: str, service_id: str, **fields) -> dict:
    url = f"{BASE_URL}/l2vpn/{VERSION}/{service_id}"
    response, status = _make_request(
        "PATCH",
        url,
        payload=fields,
        extra_headers={"Authorization": f"Bearer {token}"},
        operation="update L2VPN",
    )
    return normalize_result(response, status, "update L2VPN")


def delete_l2vpn(token: str, service_id: str) -> dict:
    url = f"{BASE_URL}/l2vpn/{VERSION}/{service_id}"
    response, status = _make_request(
        "DELETE",
        url,
        extra_headers={"Authorization": f"Bearer {token}"},
        operation="delete L2VPN",
    )
    return normalize_result(response, status, "delete L2VPN")


def get_l2vpn(token: str, service_id: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/l2vpn/{VERSION}/{service_id}"
    response, status = _make_request(
        "GET",
        url,
        extra_headers={"Authorization": f"Bearer {token}"},
        operation="get L2VPN",
    )
    return normalize_result(response, status, "get L2VPN")


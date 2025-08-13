# sdx_user_session.py

from sdxlib.token_auth import FabricTokenAuthentication as TokenAuth
from sdxlib.validator import SDXValidator
from sdxlib.exception import SDXException
from sdxlib.request import _make_request


def create_user_session(client, base_url: str, source: str = "fabric") -> dict:
    """
    Creates a user session and updates the client with user details.

    Returns:
        dict with keys: user_id, ownership, email
    """
    try:
        token = client.token_auth or TokenAuth().load_token()
        sub = token.token_sub
        ownership = SDXValidator.validate_ownership(sub)
        email = token.token_decoded.get("email")
        eppn = token.token_eppn
        given_name = token.token_given_name
        family_name = token.token_family_name
    except Exception as e:
        raise SDXException(401, "Token or ownership derivation failed", str(e))

    payload = {
        "source": source,
        "ownership": ownership,
        "email": email or "",
        "eppn": eppn or "",
        "first_name": given_name or "",
        "last_name": family_name or "",
        "role": "researcher",
    }

    url = f"{base_url}login/"
    response, status_code = _make_request("POST", url, _get_headers(client), payload, "session login")

    if not isinstance(response, dict):
        raise SDXException(500, "Invalid response format", str(response))
    if status_code != 200:
        raise SDXException(status_code, "Session login failed", str(response))

    return {
        "user_id": response.get("user_id"),
        "ownership": response.get("ownership", ownership),
        "email": response.get("email", email),
    }


def manage_services(client, method: str = "GET", service_id: str = None, data: dict = None) -> tuple:
    """
    Perform GET, POST, or DELETE on /services endpoint.

    Returns:
        tuple (response, status_code)
    """
    if not client.user_id or not client.ownership:
        return 403, None, "No session or ownership set."

    url = f"{client.base_url}services/"
    headers = _get_headers(client)

    payload = {
        "user_id": client.user_id,
        "ownership": client.ownership,
        "email": client.email,
        "source": client.source,
    }

    if service_id:
        payload["service_id"] = service_id
    if data:
        payload.update(data)

    if method == "GET":
        return _make_request("GET", url, headers, payload, "get services")
    elif method == "POST":
        return _make_request("POST", url, headers, payload, "create service")
    elif method == "DELETE":
        return _make_request("DELETE", url, headers, payload, "delete service")
    else:
        return 400, None, f"Unsupported method: {method}"


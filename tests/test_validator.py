import pytest
from sdxlib.validator import (
    validate_required_url,
    validate_name,
    is_valid_email,
    validate_notifications,
    map_http_error,
    validate_l2vpn_endpoints
)
from unittest.mock import MagicMock
from sdxlib.exception import SDXException

def test_validate_required_url_ok():
    assert validate_required_url("https://example.com") == "https://example.com"

def test_validate_required_url_fail_empty():
    with pytest.raises(ValueError, match="BASE_URL must be a non-empty string"):
        validate_required_url("   ")

def test_validate_required_url_fail_not_str():
    with pytest.raises(ValueError):
        validate_required_url(123)

def test_validate_name_ok():
    assert validate_name("my-service-name") == "my-service-name"

def test_validate_name_empty():
    with pytest.raises(ValueError, match="name must be a non-empty string"):
        validate_name("")

def test_validate_name_too_long():
    long_name = "a" * 51
    with pytest.raises(ValueError, match="name must be at most 50 characters"):
        validate_name(long_name)

def test_is_valid_email():
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("user.name@sub.domain.org") is True
    assert is_valid_email("invalid") is False           
    assert is_valid_email("no@") is False               
    assert is_valid_email("@domain") is False           
    assert is_valid_email("no@at") is True              
    assert is_valid_email(None) is False

def test_validate_notifications_none():
    assert validate_notifications(None) is None

def test_validate_notifications_valid():
    input_list = [{"email": "a@example.com"}, {"email": "b@domain.org"}]
    result = validate_notifications(input_list)
    assert result == input_list

def test_validate_notifications_too_many():
    too_many = [{"email": f"user{i}@test.com"} for i in range(11)]
    with pytest.raises(ValueError, match="notifications can contain at most 10 entries"):
        validate_notifications(too_many)

def test_validate_notifications_invalid_email():
    invalid = [{"email": "bad-email"}]
    with pytest.raises(ValueError, match="invalid email format"):
        validate_notifications(invalid)

def test_validate_notifications_not_dict():
    bad = [{"email": "ok@example.com"}, "not-a-dict"]
    with pytest.raises(ValueError, match="each notification must be a dict"):
        validate_notifications(bad)

def test_map_http_error_json():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"error": "bad request"}

    mock_exc = MagicMock()
    mock_exc.response = mock_response

    result = map_http_error(None, mock_exc, "create")
    assert result["status_code"] == 400
    assert result["message"] == "Invalid JSON or incomplete/incorrect body"
    assert result["details"] == {"error": "bad request"}

def test_map_http_error_text():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.text = "Server error"

    mock_exc = MagicMock()
    mock_exc.response = mock_response

    result = map_http_error(None, mock_exc, "update")
    assert result["status_code"] == 500
    assert result["message"] == "Unknown error"
    assert result["details"] == "Server error"

def test_map_http_error_text():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.text = "Server error"

    mock_exc = MagicMock()
    mock_exc.response = mock_response

    result = map_http_error(None, mock_exc, "update")
    assert result["status_code"] == 500
    assert result["message"] == "Unknown error"
    assert result["details"] == "Server error"

def test_validate_endpoints_all_unsupported():
    endpoints = [{"port_id": "p1", "vlan": "all"}, {"port_id": "p2", "vlan": "all"}]
    with pytest.raises(ValueError, match=r"'all' .* not supported"):
        validate_l2vpn_endpoints(endpoints)

from typing import List, Dict, Any

# Helper to create minimal endpoint dictionaries
def create_endpoint(port_suffix: str, vlan: str | int) -> Dict[str, Any]:
    return {"port_id": f"urn:sdx:port:{port_suffix}", "vlan": vlan}

@pytest.mark.parametrize(
    "vlan_a, vlan_b",
    [
        ("123", "123"),
        ("any", "any"),
        ("untagged", "untagged"),
    ],
    ids=["explicit_same", "any_any", "untagged_untagged"]
)
def test_l2vpn_valid_vlan_combinations(vlan_a, vlan_b):
    endpoints = [create_endpoint("A", vlan_a), create_endpoint("B", vlan_b)]
    validate_l2vpn_endpoints(endpoints)  # passes = success

@pytest.mark.parametrize(
    "vlan_a, vlan_b, expected_part",
    [
        ("any",     "100",   "mix|inconsistent|any"),
        ("untagged", "any",  "mix|inconsistent|untagged|any"),
        ("all",      "all",   "'all' is not supported|all is not supported"),
        ("all",      "200",   "'all' is not supported|all is not supported"),
    ],
    ids=["any_explicit", "untagged_any", "all_all", "all_explicit"]
)
def test_l2vpn_invalid_vlan_combinations(vlan_a, vlan_b, expected_part):
    endpoints = [create_endpoint("A", vlan_a), create_endpoint("B", vlan_b)]
    with pytest.raises(ValueError) as exc:
        validate_l2vpn_endpoints(endpoints)
    msg = str(exc.value).lower()
    assert any(p in msg for p in expected_part.split("|")), \
        f"Expected {expected_part!r} in error, got: {msg}"
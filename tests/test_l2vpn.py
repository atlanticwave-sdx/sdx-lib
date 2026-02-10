from sdxlib.l2vpn import create_l2vpn, get_l2vpn
from sdxlib.config import BASE_URL, VERSION
import pytest

BASE = f"{BASE_URL}/l2vpn/{VERSION}"

def test_create_l2vpn_success(mock_requests, mock_response):
    mock_response.status_code = 201
    mock_response.headers["Content-Type"] = "application/json"
    mock_response.json.return_value = {"id": "svc-abc123", "status": "created"}
    mock_requests.return_value = mock_response

    result = create_l2vpn(
        token="tok123",
        name="test-vpn",
        endpoints=[
            {"port_id": "urn:sdx:port:1", "vlan": "100"},
            {"port_id": "urn:sdx:port:2", "vlan": "100"} 
        ]
    )

    assert result["data"] == {"id": "svc-abc123", "status": "created"}
    assert result.get("error") is None
    mock_requests.assert_called_once_with(
        "POST", f"{BASE}", json=mock_requests.call_args[1]["json"], headers=mock_requests.call_args[1]["headers"], timeout=60
    )

def test_create_l2vpn_bad_request(mock_requests):
    with pytest.raises(ValueError, match="At least two endpoints"):
        create_l2vpn("tok", "bad", []) 
    mock_requests.assert_not_called() 

def test_get_l2vpn_not_found(mock_requests, mock_response):
    mock_response.status_code = 404
    mock_response.headers["Content-Type"] = "application/json"  
    mock_response.json.return_value = {"error": "Service not found", "detail": "No L2VPN with id svc-999"}
    mock_requests.return_value = mock_response

    result = get_l2vpn("tok", "svc-999")

    assert result["status_code"] == 404
    assert "not found" in result.get("error", "").lower()   
    assert result.get("error") == "Service not found"

def test_create_l2vpn_validation_error(mock_requests, mock_response):
    with pytest.raises(ValueError, match=r"(out of range|Invalid VLAN value).*9999"):
        create_l2vpn(
            token="tok123",
            name="test",
            endpoints=[
                {"port_id": "urn:sdx:port:1", "vlan": "9999"},
                {"port_id": "urn:sdx:port:2", "vlan": "9999"}
            ]
        )
    
    mock_requests.assert_not_called()
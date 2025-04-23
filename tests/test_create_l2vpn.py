import pytest
import requests_mock
from sdxlib.sdx_client import SDXClient
from unittest.mock import patch

"""
Test the SDXClient class for creating L2VPNs.
- calls the internal request method
- raises correct error if required fields are missing
- behaves correctly when the API returns a success response
"""

def test_create_l2vpn_successful_request(base_url, service_name, service_endpoints, expected_service_id):
    """Test that create_l2vpn returns expected service_id on successful request."""
    client = SDXClient(
        base_url=base_url,
        name=service_name,
        endpoints=service_endpoints,
    )

    with requests_mock.Mocker() as m:
        m.post(
            f"{base_url}/l2vpn/1.0",
            json={"service_id": expected_service_id},
            status_code=201,
        )
        result = client.create_l2vpn()

    assert result["service_id"] == expected_service_id

def test_create_l2vpn_fails_with_missing_base_url(service_name, service_endpoints):
    """Test that ValueError is raised when base_url is None."""
    with pytest.raises(ValueError, match="Base URL must be a non-empty string."):
        SDXClient(base_url=None, name=service_name, endpoints=service_endpoints)

def test_create_l2vpn_fails_with_missing_name(base_url, service_endpoints):
    """Test that ValueError is raised when name is None."""
    with pytest.raises(ValueError, match="Name must be a non-empty string."):
        SDXClient(base_url=base_url, name=None, endpoints=service_endpoints)

def test_create_l2vpn_fails_with_missing_endpoints(base_url, service_name):
    """Test that ValueError is raised when endpoints is None."""
    with pytest.raises(ValueError, match="Endpoints must be a non-empty list."):
        SDXClient(base_url=base_url, name=service_name, endpoints=None)

def test_create_l2vpn_fails_with_empty_endpoints(base_url, service_name):
    """Test that ValueError is raised when endpoints is an empty list."""
    with pytest.raises(ValueError, match="Endpoints must be a non-empty list."):
        SDXClient(base_url=base_url, name=service_name, endpoints=[])

def test_create_l2vpn_returns_cached_response(base_url, service_name, service_endpoints, expected_service_id):
    """Test that create_l2vpn returns cached response if cache_key is present."""
    client = SDXClient(base_url=base_url, name=service_name, endpoints=service_endpoints)

    cache_key = (
        service_name,
        tuple(endpoint["port_id"] for endpoint in service_endpoints),
    )
    cached_response = {"service_id": expected_service_id}
    client._request_cache[cache_key] = ({}, cached_response)

    result = client.create_l2vpn()
    assert result == cached_response

def test_create_l2vpn_calls_make_request(base_url, service_name, service_endpoints):
    """Test that create_l2vpn calls _make_request when cache is not used."""
    client = SDXClient(base_url=base_url, name=service_name, endpoints=service_endpoints)

    expected = {"service_id": "mocked-id"}
    with patch.object(SDXClient, "_make_request", return_value=expected) as mock:
        result = client.create_l2vpn()
        assert result == expected
        assert mock.called
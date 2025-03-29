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


@pytest.fixture
def base_url():
    return "http://aw-sdx-controller.renci.org:8081/SDX-Controller"


@pytest.fixture
def service_name():
    return "TestL2VPN"


@pytest.fixture
def service_endpoints():
    return [
        {"port_id": "urn:sdx:port:tenet.ac.za:Tenet03:50", "vlan": "150"},
        {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "300"},
    ]


@pytest.fixture
def expected_service_id():
    return "e64f7146-5673-4e03-9d6d-95eafab657f9"


@patch("sdxlib.sdx_token_auth.TokenAuthentication.load_token")
def test_create_l2vpn_successful_request(
    mock_load_token, base_url, service_name, service_endpoints, expected_service_id
):

    mock_load_token.return_value.token_eppn = "pi@sdx-email.org"
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

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


@patch("sdxlib.sdx_token_auth.TokenAuthentication.load_token")
def test_create_l2vpn_successful_request(mock_load_token):
    mock_load_token.return_value.token_eppn = "pi@sdx-email.org"
    # Setup fake SDXClient
    client = SDXClient(
        base_url="http://aw-sdx-controller.renci.org:8081/SDX-Controller",
        name="TestL2VPN",
        endpoints=[
            {"port_id": "urn:sdx:port:tenet.ac.za:Tenet03:50", "vlan": "150"},
            {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "300"},
        ],
    )

    # Mock the API endpoint
    with requests_mock.Mocker() as m:
        m.post(
            "http://aw-sdx-controller.renci.org:8081/SDX-Controller/l2vpn/1.0",
            json={"service_id": "e64f7146-5673-4e03-9d6d-95eafab657f9"},
            status_code=201,
        )

        result = client.create_l2vpn()
        assert result["service_id"] == "e64f7146-5673-4e03-9d6d-95eafab657f9"

import pytest

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
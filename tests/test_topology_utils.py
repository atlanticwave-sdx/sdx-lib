from sdxlib.topology_utils import (
    _parse_vlan_value,
    _collapse_ints_to_ranges,
    _iter_advertised_vlan_ints,
    get_topology,
    _get_vlans_in_use,
    get_available_ports,
)

def test_parse_vlan_value():
    assert _parse_vlan_value(200) == [200]
    assert _parse_vlan_value("777") == [777]
    assert _parse_vlan_value("100-103") == [100, 101, 102, 103]
    assert _parse_vlan_value("500:503") == [500, 501, 502, 503]
    assert _parse_vlan_value("10,20-22,30") == [10, 20, 21, 22, 30]
    assert _parse_vlan_value("invalid") == []
    assert _parse_vlan_value(None) == []

def test_collapse_ints_to_ranges():
    assert _collapse_ints_to_ranges([]) == "None"
    assert _collapse_ints_to_ranges([42]) == "42"
    assert _collapse_ints_to_ranges([100, 101, 102, 104]) == "100-102, 104"
    assert _collapse_ints_to_ranges([5, 6, 7, 8, 9]) == "5-9"

def test_iter_advertised_vlan_ints():
    assert list(_iter_advertised_vlan_ints(["100-102"])) == [100, 101, 102]
    assert list(_iter_advertised_vlan_ints([[200, 203]])) == [200, 201, 202, 203]
    assert list(_iter_advertised_vlan_ints([])) == []

def test_get_topology_success(mocker, mock_requests, mock_response):
    mock_response.status_code = 200
    mock_response.json.return_value = {"nodes": [], "links": []}
    mock_requests.return_value = mock_response

    result = get_topology("tok123")

    assert isinstance(result, dict)
    assert "status_code" in result
    assert result["status_code"] == 200

def test_get_vlans_in_use(mocker):
    fake_l2vpns = [
        {"endpoints": [{"port_id": "p1", "vlan": "100-102"}, {"port_id": "p2", "vlan": "500"}]},
        {"endpoints": [{"port_id": "p1", "vlan": "200"}]},
    ]
    mocker.patch("sdxlib.topology_utils.get_all_l2vpns", return_value=fake_l2vpns)

    usage = _get_vlans_in_use("tok")
    assert usage["p1"] == [100, 101, 102, 200]
    assert usage["p2"] == [500]

def test_get_available_ports_with_used_vlans( mocker):
    mock_topology = {
        "nodes": [
            {
                "id": "urn:sdx:node:example:swA",
                "name": "Switch A",
                "ports": [
                    {
                        "id": "urn:sdx:port:example:swA:eth1",
                        "name": "Eth1 Customer",
                        "status": "up",
                        "nni": False,
                        "entities": ["customer-group-1"],
                        "services": {
                            "l2vpn_ptp": {
                                "vlan_range": ["100-200"]
                            }
                        }
                    }
                ]
            }
        ]
    }

    mocker.patch(
        "sdxlib.topology_utils.get_topology",
        return_value=mock_topology 
    )

    mocker.patch(
        "sdxlib.topology_utils.get_all_l2vpns",
        return_value=[
            {
                "service_id": "svc-123",
                "name": "Test VPN",
                "endpoints": [
                    {"port_id": "urn:sdx:port:example:swA:eth1", "vlan": "150"}
                ]
            }
        ]
    )

    mocker.patch(
        "sdxlib.topology_utils._get_vlans_in_use",
        return_value={
            "urn:sdx:port:example:swA:eth1": [150]
        }
    )

    ports = get_available_ports("tok")

    assert isinstance(ports, list)
    assert len(ports) == 1, f"Ports - {len(ports)}: {ports}"

    if ports:
        port_info = ports[0]
        assert port_info["Port ID"] == "urn:sdx:port:example:swA:eth1"
        assert port_info["Status"] == "up"
        assert "150" in port_info["VLANs in Use"]
        assert "100-149" in port_info["VLANs Available"] or "100-149, 151-200" == port_info["VLANs Available"]
        assert "151-200" in port_info["VLANs Available"] or "100-149, 151-200" == port_info["VLANs Available"]

def test_get_available_ports_no_l2vpns(mocker):
    mock_topology_data = {
        "nodes": [
            {
                "id": "urn:sdx:node:example:nodeA",
                "name": "Node A",
                "ports": [
                    {
                        "id": "urn:sdx:port:example:sw1:eth1",
                        "name": "Customer Eth1",
                        "status": "up",
                        "nni": False,
                        "entities": ["customer-entity-1"],
                        "services": {
                            "l2vpn_ptp": {
                                "vlan_range": ["100-200"]
                            }
                        }
                    }
                ]
            }
        ]
    }

    mocker.patch(
        "sdxlib.topology_utils.get_topology",
        return_value=mock_topology_data
    )

    mocker.patch("sdxlib.topology_utils.get_all_l2vpns", return_value=[])
    mocker.patch("sdxlib.topology_utils._get_vlans_in_use", return_value={})

    ports = get_available_ports("tok")

    assert isinstance(ports, list)
    assert len(ports) >= 1, f"No ports: {ports}"

    if ports:
        p = ports[0]
        assert p["Port ID"] == "urn:sdx:port:example:sw1:eth1"
        assert p["Domain"] == "example"
        assert p["Device"] == "sw1"
        assert p["Port"] == "eth1"
        assert p["VLANs Available"] == "100-200"
        assert p["VLANs in Use"] == "None"

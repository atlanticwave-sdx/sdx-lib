import unittest
import json
from sdxlib.sdx_response import SDXResponse


class TestSDXResponseMethods(unittest.TestCase):
    def test_str_method(self):
        """Test the string output of the SDXResponse.__str__ method."""

        self.maxDiff = None

        response_data = {
            "service_id": "12345",
            "name": "VLAN between AMPATH/300 and TENET/150",
            "endpoints": [
                {"port_id": "urn:sdx:port:tenet.ac.za:Tenet03:50", "vlan": "150"},
                {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "300"},
            ],
            "description": "This is an example to demonstrate a L2VPN with optional attributes",
            "qos_metrics": {
                "min_bw": {"value": 5, "strict": False},
                "max_delay": {"value": 150, "strict": True},
            },
            "notifications": [
                {"email": "user@domain.com"},
                {"email": "user2@domain2.com"},
            ],
            "ownership": "user1",
            "creation_date": "2024-01-01T10:00:00",
            "archived_date": "0",
            "status": "active",
            "state": "up",
            "counters_location": "location1",
            "last_modified": "2024-01-01T10:00:00",
            "current_path": ["path1"],
            "oxp_service_ids": [{"id": "oxp1"}, {"id": "oxp2"}],
            "scheduling": None,
        }

        response = SDXResponse(response_data)

        expected_str = json.dumps(response_data, indent=4, sort_keys=True)
        actual_str = json.dumps(vars(response), indent=4, sort_keys=True)

        self.assertEqual(actual_str, expected_str)

    def test_eq_method(self):
        """Test the equality comparison of two SDXResponse objects."""
        response1 = SDXResponse(
            {
                "service_id": "12345",
                "ownership": "user1",
                "creation_date": "2024-01-01T10:00:00",
                "archived_date": "0",
                "status": "active",
                "state": "up",
                "counters_location": "location1",
                "last_modified": "2024-01-01T10:00:00",
                "current_path": ["path1"],
                "oxp_service_ids": [{"id": "oxp1"}, {"id": "oxp2"}],
            }
        )

        response2 = SDXResponse(
            {
                "service_id": "12345",
                "ownership": "user1",
                "creation_date": "2024-01-01T10:00:00",
                "archived_date": "0",
                "status": "active",
                "state": "up",
                "counters_location": "location1",
                "last_modified": "2024-01-01T10:00:00",
                "current_path": ["path1"],
                "oxp_service_ids": [{"id": "oxp1"}, {"id": "oxp2"}],
            }
        )

        # Test for equality (should be True)
        self.assertEqual(response1, response2)

        # Test for inequality by changing a field (should be False)
        response3 = SDXResponse(
            {
                "service_id": "54321",
                "ownership": "user2",
                "creation_date": "2024-01-01T11:00:00",
                "archived_date": "0",
                "status": "inactive",
                "state": "down",
                "counters_location": "location2",
                "last_modified": "2024-01-01T11:00:00",
                "current_path": ["path2"],
                "oxp_service_ids": [{"id": "oxp3"}],
            }
        )

        self.assertNotEqual(response1, response3)


if __name__ == "__main__":
    unittest.main()

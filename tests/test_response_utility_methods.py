import unittest
from sdxlib.sdx_response import SDXResponse


class TestSDXResponseMethods(unittest.TestCase):
    def test_str_method(self):
        """Test the string output of the SDXResponse.__str__ method."""
        response = SDXResponse(
            {
                "service_id": "12345",
                "ownership": "user1",
                "creation_date": "2024-01-01T10:00:00",
                "archived_date": None,
                "status": "active",
                "state": "up",
                "counters_location": "location1",
                "last_modified": "2024-01-01T10:00:00",
                "current_path": ["path1"],
                "oxp_service_ids": [{"id": "oxp1"}, {"id": "oxp2"}],
            }
        )

        expected_str = (
            "L2VPN Response:\n"
            "        service_id: 12345\n"
            "        ownership: user1\n"
            "        creation_date: 2024-01-01T10:00:00\n"
            "        archived_date: None\n"
            "        status: active\n"
            "        state: up\n"
            "        counters_location: location1\n"
            "        last_modified: 2024-01-01T10:00:00\n"
            "        current_path: path1\n"
            "        oxp_service_ids: ['oxp1', 'oxp2']"
        )

        self.assertEqual(str(response), expected_str)

    def test_eq_method(self):
        """Test the equality comparison of two SDXResponse objects."""
        response1 = SDXResponse(
            {
                "service_id": "12345",
                "ownership": "user1",
                "creation_date": "2024-01-01T10:00:00",
                "archived_date": None,
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
                "archived_date": None,
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
                "archived_date": None,
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

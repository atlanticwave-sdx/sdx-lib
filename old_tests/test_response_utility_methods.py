import logging
import unittest
import json
from sdxlib.sdx_response import SDXResponse
from test_config import TEST_SERVICE_ID, TEST_NAME, TEST_ENDPOINTS


class TestSDXResponseMethods(unittest.TestCase):
    def test_str_method(self):
        """Test the string output of the SDXResponse.__str__ method."""

        self.maxDiff = None

        response_data = {
            "service_id": TEST_SERVICE_ID,
            "name": TEST_NAME,
            "endpoints": TEST_ENDPOINTS,
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
            "status": "up",
            "state": "enabled",
            "counters_location": "location1",
            "last_modified": "2024-01-01T10:00:00",
            "current_path": ["path1"],
            "oxp_service_ids": {"provider1": ["oxp1"], "provider2": ["oxp2"],},
            "scheduling": None,
        }

        response = SDXResponse(response_data)
        serializable_dict = {
            key: value
            for key, value in vars(response).items()
            if not isinstance(value, logging.Logger)
        }

        expected_str = json.dumps(response_data, indent=4, sort_keys=True)
        actual_str = json.dumps(serializable_dict, indent=4, sort_keys=True)

        self.assertEqual(actual_str, expected_str)

    def test_eq_method(self):
        """Test the equality comparison of two SDXResponse objects."""
        response1 = SDXResponse(
            {
                "service_id": TEST_SERVICE_ID,
                "name": TEST_NAME,
                "endpoints": TEST_ENDPOINTS,
                "ownership": "user1",
                "creation_date": "2024-01-01T10:00:00",
                "archived_date": "0",
                "status": "up",
                "state": "enabled",
                "counters_location": "location1",
                "last_modified": "2024-01-01T10:00:00",
                "current_path": ["path1"],
                "oxp_service_ids": {"provider1": ["oxp1"], "provider2": ["oxp2"],},
            }
        )

        response2 = SDXResponse(
            {
                "service_id": TEST_SERVICE_ID,
                "name": TEST_NAME,
                "endpoints": TEST_ENDPOINTS,
                "ownership": "user1",
                "creation_date": "2024-01-01T10:00:00",
                "archived_date": "0",
                "status": "up",
                "state": "enabled",
                "counters_location": "location1",
                "last_modified": "2024-01-01T10:00:00",
                "current_path": ["path1"],
                "oxp_service_ids": {"provider1": ["oxp1"], "provider2": ["oxp2"],},
            }
        )

        # Test for equality (should be True)
        self.assertEqual(response1, response2)

        # Test for inequality by changing a field (should be False)
        response3 = SDXResponse(
            {
                "service_id": "54321",
                "name": "Different L2VPN",
                "endpoints": TEST_ENDPOINTS,
                "ownership": "user2",
                "creation_date": "2024-01-01T11:00:00",
                "archived_date": "0",
                "status": "down",
                "state": "disabled",
                "counters_location": "location2",
                "last_modified": "2024-01-01T11:00:00",
                "current_path": ["path2"],
                "oxp_service_ids": {"provider3": ["oxp3"],},
            }
        )

        self.assertNotEqual(response1, response3)


if __name__ == "__main__":
    unittest.main()

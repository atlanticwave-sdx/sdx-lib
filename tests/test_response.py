import json
import unittest
from sdxlib.sdx_response import SDXResponse
from test_config import *


class SDXResponseTest(unittest.TestCase):

    def setUp(self):
        """Initialize a valid SDXResponse object for testing."""
        self.response = SDXResponse(MOCK_RESPONSE[list(MOCK_RESPONSE.keys())[0]])
    
    def test_response_initialization_with_valid_json(self):
        response_json = TEST_VALID_RESPONSE
        response = SDXResponse(response_json)
        self.assertEqual(response.service_id, TEST_SERVICE_ID)
        self.assertEqual(response.name, TEST_NAME)
        self.assertEqual(response.endpoints, TEST_ENDPOINTS)
        self.assertEqual(response.ownership, TEST_OWNERSHIP)
        self.assertEqual(response.creation_date, TEST_CREATION_DATE)
        self.assertEqual(response.archived_date, TEST_ARCHIVED_DATE)
        self.assertEqual(response.status, TEST_STATUS)
        self.assertEqual(response.state, TEST_STATE)
        self.assertEqual(response.counters_location, TEST_COUNTERS_LOCATION)
        self.assertEqual(response.last_modified, TEST_LAST_MODIFIED)
        self.assertEqual(response.current_path, TEST_CURRENT_PATH)
        self.assertEqual(response.oxp_service_ids, TEST_OXP_SERVICE_IDS)


    def test_response_initialization_with_missing_attributes(self):
        response_json = TEST_MISSING_ATTRIBUTES_RESPONSE
        response = SDXResponse(response_json)
        self.assertIsNone(response.scheduling)
        self.assertIsNone(response.description)

    def test_response_initialization_with_invalid_json(self):
        response_json = "invalid_json"
        with self.assertRaises(TypeError):
            SDXResponse(response_json)

    def test_valid_sdx_response(self):
        """Test that a valid SDXResponse object initializes correctly."""
        self.assertEqual(self.response.service_id, MOCK_RESPONSE[self.response.service_id]["service_id"])
        self.assertEqual(self.response.name, MOCK_RESPONSE[self.response.service_id]["name"])
        self.assertEqual(self.response.status, "up")
    
    def test_missing_required_field(self):
        """Test that missing required fields raise ValueError."""
        invalid_response = MOCK_RESPONSE[self.response.service_id].copy()
        del invalid_response["name"]  # Remove required field
        with self.assertRaises(ValueError) as context:
            SDXResponse(invalid_response)
        self.assertIn("Missing required field: name", str(context.exception))
    
    def test_invalid_field_type(self):
        """Test that incorrect field types raise ValueError."""
        invalid_response = MOCK_RESPONSE[self.response.service_id].copy()
        invalid_response["endpoints"] = "invalid_type"  # Should be a list
        with self.assertRaises(ValueError) as context:
            SDXResponse(invalid_response)
        expected_message = "Invalid type for endpoints: Expected list, got str"
        self.assertIn(expected_message, str(context.exception))
    
    def test_string_representation(self):
        """Test that __str__ returns valid JSON output."""
        response_str = str(self.response)
        try:
            json.loads(response_str)  # Validate JSON format
        except json.JSONDecodeError:
            self.fail("SDXResponse __str__ method does not return valid JSON.")
    
    def test_equality(self):
        """Test that SDXResponse objects with the same data are equal."""
        another_response = SDXResponse(MOCK_RESPONSE[self.response.service_id])
        self.assertEqual(self.response, another_response)

    def test_sdx_response_with_invalid_state(self):
        """Test that an invalid state value raises a ValueError."""
        invalid_response = TEST_VALID_RESPONSE.copy()
        invalid_response["state"] = "invalid_state"
        with self.assertRaises(ValueError) as context:
            SDXResponse(invalid_response)
        self.assertIn("Invalid state", str(context.exception))
    
    def test_sdx_response_with_invalid_status(self):
        """Test that an invalid status value raises a ValueError."""
        invalid_response = TEST_VALID_RESPONSE.copy()
        invalid_response["status"] = "invalid_status"
        with self.assertRaises(ValueError) as context:
            SDXResponse(invalid_response)
        self.assertIn("Invalid status", str(context.exception))
    
    def test_sdx_response_with_invalid_json_format(self):
        """Test that passing a non-dictionary JSON raises a TypeError."""
        with self.assertRaises(TypeError):
            SDXResponse("this is not a dictionary")
    
    def test_sdx_response_missing_required_key(self):
        """Test that missing a required key raises a ValueError."""
        invalid_response = TEST_VALID_RESPONSE.copy()
        del invalid_response["service_id"]
        with self.assertRaises(ValueError) as context:
            SDXResponse(invalid_response)
        self.assertIn("Missing required field: service_id", str(context.exception))
    
    
if __name__ == "__main__":
    unittest.main()
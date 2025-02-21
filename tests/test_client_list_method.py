import unittest
from unittest.mock import patch, Mock
from sdxlib.sdx_client import SDXClient
from sdxlib.sdx_exception import SDXException
from sdxlib.sdx_response import SDXResponse
from requests.exceptions import HTTPError, Timeout, RequestException
from test_config import (
    TEST_URL,
    TEST_NAME,
    TEST_ENDPOINTS,
    TEST_SERVICE_ID,
    MOCK_RESPONSE,
)


class TestSDXClient(unittest.TestCase):
    def setUp(self):
        self.client = SDXClient(base_url=TEST_URL)

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_l2vpn_success(self, mock_get_logger, mock_get):
        """Test successful retrieval of an L2VPN."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            TEST_SERVICE_ID: {
                "service_id": TEST_SERVICE_ID,
                "name": "Test L2VPN",
                "ownership": "user1",
                "endpoints": TEST_ENDPOINTS,
                "creation_date": "20240522T00:00:00Z",
                "archived_date": "0",
                "status": "active",
                "state": "up",
                "counters_location": "https://my.aw-sdx.net/l2vpn/7cdf23e8978c",
                "last_modified": "0",
                "current_path": ["path1"],
                "oxp_service_ids": {"provider1": ["oxp1"], "provider2": ["oxp2"],},
            }
        }
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL)

        result = client.get_l2vpn(TEST_SERVICE_ID)

        # Check correct URL was used
        expected_url = f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}"
        mock_get.assert_called_with(
            expected_url, auth=(None, None), verify=True, timeout=120
        )

        # Check correct data retrieval
        self.assertEqual(result["service_id"].iloc[0], TEST_SERVICE_ID)
        self.assertEqual(result["name"].iloc[0], "Test L2VPN")

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_l2vpn_logging_success(self, mock_get_logger, mock_get):
        """Test logging of successful L2VPN retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "8344657b-2466-4735-9a21-143643073865": {
                "service_id": "8344657b-2466-4735-9a21-143643073865",
                "name": "VLAN between AMPATH/300 and TENET/150",
                "ownership": "user1",
                "endpoints": [
                    {"port_id": "urn:sdx:port:tenet.ac.za:Tenet03:50", "vlan": "150"},
                    {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "300"},
                ],
                "creation_date": "20240522T00:00:00Z",
                "archived_date": "20240101T00:00:00Z",
                "status": "up",
                "state": "enabled",
                "counters_location": "https://my.aw-sdx.net/l2vpn/7cdf23e8978c",
                "last_modified": "0",
                "current_path": ["urn:sdx:link:tenet.ac.za:LinkToAmpath"],
                "oxp_service_ids": {
                    "ampath.net": ["c73da8e1"],
                    "tenet.ac.za": ["5d034620"],
                },
                "qos_metrics": {
                    "max_delay": {"strict": True, "value": 150},
                    "min_bw": {"strict": False, "value": 5},
                },
                "scheduling": None,
                "notifications": [
                    {"email": "user@domain.com"},
                    {"email": "user2@domain2.com"},
                ],
                "description": None,
            }
        }

        mock_get.return_value = mock_response
        mock_logger = Mock()

        mock_get_logger.return_value = mock_logger
        client = SDXClient(
            base_url=TEST_URL,
            name=TEST_NAME,
            endpoints=TEST_ENDPOINTS,
            logger=mock_logger,
        )

        client.get_l2vpn(TEST_SERVICE_ID)
        expected_message = (
            f"L2VPN retrieval request sent to {TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}."
        )
        expected_full_response = f"Full response: {mock_response.json.return_value}"

        mock_logger.info.assert_any_call(expected_message)
        mock_logger.info.assert_any_call(expected_full_response)

    @patch("requests.get")
    def test_get_l2vpn_404_error(self, mock_get):
        """Test handling of 404 error for L2VPN retrieval."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_response.json.return_value = {"error": "Service not found"}
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL)

        with self.assertRaises(SDXException) as context:
            client.get_l2vpn("invalid_id")

        self.assertIn("Service ID not found", str(context.exception))

    @patch("requests.get")
    def test_get_l2vpn_401_error(self, mock_get):
        """Test handling of 401 error for L2VPN retrieval."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        client = SDXClient(
            base_url=TEST_URL,
            name=TEST_NAME,
            endpoints=TEST_ENDPOINTS,
            logger=mock_response,
        )

        with self.assertRaises(SDXException):
            client.get_l2vpn(TEST_SERVICE_ID)

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_l2vpn_logging_404_error(self, mock_get_logger, mock_get):
        """Test logging of 404 error for L2VPN retrieval."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        client = SDXClient(
            base_url=TEST_URL,
            name=TEST_NAME,
            endpoints=TEST_ENDPOINTS,
            logger=mock_logger,
        )

        with self.assertRaises(SDXException):
            client.get_l2vpn("invalid_id")
        mock_get_logger().error.assert_called_with(
            "Failed to retrieve L2VPN. Status code: 404: Service ID not found"
        )

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_l2vpn_logging_401_error(self, mock_get_logger, mock_get):
        """Test logging of 401 error for L2VPN retrieval."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        client = SDXClient(
            base_url=TEST_URL,
            name=TEST_NAME,
            endpoints=TEST_ENDPOINTS,
            logger=mock_logger,
        )

        with self.assertRaises(SDXException):
            client.get_l2vpn(TEST_SERVICE_ID)
        mock_get_logger().error.assert_called_with(
            "Failed to retrieve L2VPN. Status code: 401: Not Authorized"
        )

    @patch("requests.get")
    def test_get_l2vpn_request_exception(self, mock_get):
        """Test handling of request exceptions during L2VPN retrieval."""
        mock_get.side_effect = RequestException("Network error")
        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS,)
        with self.assertRaises(SDXException):
            client.get_l2vpn(TEST_SERVICE_ID)

    @patch("requests.get")
    def test_get_l2vpn_json_parsing_error(self, mock_get):
        """Test handling of JSON parsing errors during L2VPN retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS,)

        with self.assertRaises(SDXException):
            client.get_l2vpn(TEST_SERVICE_ID)

    @patch("requests.get")
    def test_get_l2vpn_valid_url_construction(self, mock_get):
        """Test valid URL construction for L2VPN retrieval."""
        # Prepare the mock response to return the expected structure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_RESPONSE

        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS)

        # Call the get_l2vpn method
        result = client.get_l2vpn(TEST_SERVICE_ID)

        # Assert the URL was called correctly
        expected_url = f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}"
        mock_get.assert_called_with(
            expected_url, auth=(None, None), verify=True, timeout=120
        )

        # Assert the result is as expected
        self.assertEqual(result["service_id"].iloc[0], TEST_SERVICE_ID)
        self.assertEqual(result["name"].iloc[0], TEST_NAME)

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_all_l2vpns_active(self, mock_get_logger, mock_get):
        """Test retrieving active L2VPNs."""

        self.maxDiff = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_RESPONSE
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL)
        result = client.get_all_l2vpns(archived=False, format="json")

        actual_result = {
            service_id: {
                key: value
                for key, value in (
                    vars(response) if isinstance(response, SDXResponse) else response
                ).items()
                if key != "_logger" and value is not None
            }
            for service_id, response in result.items()
        }

        expected_result = {
            service_id: {key: value for key, value in data.items() if value is not None}
            for service_id, data in MOCK_RESPONSE.items()
        }

        self.assertEqual(actual_result, expected_result)

        mock_get_logger().info.assert_called_with(
            f"Retrieved L2VPNs successfully: {MOCK_RESPONSE}"
        )

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_all_l2vpns_archived(self, mock_get_logger, mock_get):
        """Test retrieving archived L2VPNs."""

        self.maxDiff = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "8344657b-2466-4735-9a21-143643073865": {
                "service_id": "8344657b-2466-4735-9a21-143643073865",
                "name": "VLAN between AMPATH/300 and TENET/150",
                "ownership": "user1",
                "endpoints": [
                    {"port_id": "urn:sdx:port:tenet.ac.za:Tenet03:50", "vlan": "150"},
                    {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "300"},
                ],
                "creation_date": "20240522T00:00:00Z",
                "archived_date": "20240101T00:00:00Z",
                "status": "up",
                "state": "enabled",
                "counters_location": "https://my.aw-sdx.net/l2vpn/7cdf23e8978c",
                "last_modified": "0",
                "current_path": ["urn:sdx:link:tenet.ac.za:LinkToAmpath"],
                "oxp_service_ids": {
                    "ampath.net": ["c73da8e1"],
                    "tenet.ac.za": ["5d034620"],
                },
                "qos_metrics": {
                    "max_delay": {"strict": True, "value": 150},
                    "min_bw": {"strict": False, "value": 5},
                },
                "scheduling": None,
                "notifications": [
                    {"email": "user@domain.com"},
                    {"email": "user2@domain2.com"},
                ],
                "description": None,
            }
        }

        mock_get.return_value = mock_response
        client = SDXClient(base_url=TEST_URL)
        result = client.get_all_l2vpns(archived=True, format="json")

        cleaned_result = {
            service_id: {
                key: value
                for key, value in (
                    vars(response) if isinstance(response, SDXResponse) else response
                ).items()
                if key != "_logger"
            }
            for service_id, response in result.items()
        }

        expected_result = {
            service_id: data
            for service_id, data in mock_response.json.return_value.items()
        }

        self.assertEqual(cleaned_result, expected_result)

        mock_get_logger().info.assert_called_with(
            "Retrieved L2VPNs successfully: {}".format(mock_response.json.return_value)
        )

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_all_l2vpns_logging_retrieval(self, mock_get_logger, mock_get):
        """Test logging of L2VPN retrieval."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "8344657b-2466-4735-9a21-143643073865": {
                "service_id": "8344657b-2466-4735-9a21-143643073865",
                "name": "VLAN between AMPATH/300 and TENET/150",
                "ownership": "user1",
                "endpoints": [
                    {"port_id": "urn:sdx:port:tenet.ac.za:Tenet03:50", "vlan": "150"},
                    {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "300"},
                ],
                "creation_date": "20240522T00:00:00Z",
                "archived_date": "20240101T00:00:00Z",
                "status": "up",
                "state": "enabled",
                "counters_location": "https://my.aw-sdx.net/l2vpn/7cdf23e8978c",
                "last_modified": "0",
                "current_path": ["urn:sdx:link:tenet.ac.za:LinkToAmpath"],
                "oxp_service_ids": {
                    "ampath.net": ["c73da8e1"],
                    "tenet.ac.za": ["5d034620"],
                },
                "qos_metrics": {
                    "max_delay": {"strict": True, "value": 150},
                    "min_bw": {"strict": False, "value": 5},
                },
                "scheduling": None,
                "notifications": [
                    {"email": "user@domain.com"},
                    {"email": "user2@domain2.com"},
                ],
                "description": None,
            }
        }

        mock_get.return_value = mock_response
        client = SDXClient(base_url=TEST_URL)

        client.get_all_l2vpns()

        expected_log_message = (
            f"Retrieved L2VPNs successfully: {mock_response.json.return_value}"
        )

        mock_get_logger().info.assert_called_with(expected_log_message)

    @patch("requests.get")
    def test_get_all_l2vpns_empty_list(self, mock_get):
        """Test handling of empty L2VPN list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS,)

        result = client.get_all_l2vpns(format="dataframe")
        self.assertTrue(result.empty)

    @patch("requests.get")
    def test_get_all_l2vpns_request_exception(self, mock_get):
        """Test handling of request exceptions during L2VPN retrieval."""
        mock_get.side_effect = RequestException("Network error")

        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS,)

        with self.assertRaises(SDXException):
            client.get_all_l2vpns()

    @patch("requests.get")
    @patch("logging.getLogger")
    def test_get_all_l2vpns_logging_error_conditions(self, mock_get_logger, mock_get):
        """Test logging of error conditions for retrieving L2VPNs."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS,)

        with self.assertRaises(SDXException):
            client.get_all_l2vpns(archived=True)
        mock_get_logger().error.assert_called_with(
            "Failed to retrieve L2VPNs. Status code: 404: Unknown error occurred."
        )

    @patch("requests.get")
    def test_get_all_l2vpns_empty_json_response(self, mock_get):
        """Test handling of empty JSON response for retrieving all L2VPN"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        client = SDXClient(base_url=TEST_URL, name=TEST_NAME, endpoints=TEST_ENDPOINTS,)

        result = client.get_all_l2vpns(archived=False, format="json")
        self.assertEqual(result, {})


# Run the tests
if __name__ == "__main__":
    unittest.main()

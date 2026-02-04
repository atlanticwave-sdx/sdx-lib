import unittest
from unittest.mock import patch, Mock
from sdxlib.sdx_client import SDXClient
from test_config import (
    TEST_URL,
    TEST_NAME,
    TEST_ENDPOINTS,
    TEST_SERVICE_ID,
    MOCK_RESPONSE,
    create_client,
)


class TestSDXClientAuth(unittest.TestCase):
    """
    Unit tests for SDXClient authentication and API calls.
    Verifies both authenticated and unauthenticated requests.
    """

    def setUp(self):
        """Setup common test data and initialize clients."""
        # Create an authenticated client with username and password
        self.auth_client = create_client(
            base_url=TEST_URL,
            name=TEST_NAME,
            endpoints=TEST_ENDPOINTS,
            http_username="testuser",
            http_password="testpassword",
        )
        # Create a default (unauthenticated) client
        self.default_client = create_client(base_url=TEST_URL, name=TEST_NAME)

    def _test_auth(self, method, client, url, mock_request, **kwargs):
        """
        Generic helper function to test the auth parameter for API methods.

        Args:
            method (str): HTTP method (e.g., 'get', 'post', 'delete', 'patch').
            client (SDXClient): SDXClient instance to use for the call.
            url (str): The expected URL for the request.
            mock_request (Mock): Mocked requests method.
            **kwargs: Additional arguments for the request (e.g., payload).
        """
        # Mock the response object
        mock_response = Mock()
        mock_response.json.return_value = {"service_id": "123", "name": "TestL2VPN"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Extract payload if present
        json_payload = kwargs.pop("json", None)

        # Call the method dynamically based on the name
        client_method = getattr(client, method)
        client_method(**kwargs)

        # Determine expected authentication credentials
        expected_auth = (
            ("testuser", "testpassword") if client == self.auth_client else None
        )

        # Verify the request was called with the expected parameters
        mock_request.assert_called_once_with(
            url,
            auth=expected_auth,  # Check if auth matches the client type
            verify=True,
            timeout=120,
            json=json_payload,  # Include the payload in the expected call
        )


@patch("requests.post")
def test_create_l2vpn_with_and_without_auth(self, mock_post):
    """Test create_l2vpn with and without authentication."""
    mock_response = Mock()
    mock_response.json.return_value = {"service_id": "123"}
    mock_response.status_code = 201
    mock_post.return_value = mock_response

    # Test with authentication
    self.auth_client.description = "Test Description"
    self._test_auth(
        method="create_l2vpn",
        client=self.auth_client,
        url=f"{TEST_URL}/l2vpn/1.0",
        mock_request=mock_post,
        json={
            "name": TEST_NAME,
            "endpoints": TEST_ENDPOINTS,
            "description": "Test Description",
        },
    )
    mock_post.reset_mock()

    # Test without authentication
    self.default_client.name = TEST_NAME
    self.default_client.endpoints = TEST_ENDPOINTS
    self._test_auth(
        method="create_l2vpn",
        client=self.default_client,
        url=f"{TEST_URL}/l2vpn/1.0",
        mock_request=mock_post,
        json={"name": TEST_NAME, "endpoints": TEST_ENDPOINTS,},
    )

    @patch("requests.get")
    def test_get_l2vpn_with_and_without_auth(self, mock_get):
        """Test get_l2vpn with and without authentication."""
        # Mock the response for the L2VPN retrieval
        mock_get.return_value.json.return_value = MOCK_RESPONSE[TEST_SERVICE_ID]

        # Test with authentication
        self._test_auth(
            method="get_l2vpn",
            client=self.auth_client,
            url=f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}",
            mock_request=mock_get,
            service_id=TEST_SERVICE_ID,
        )

        # Reset mock for the unauthenticated call
        mock_get.reset_mock()

        # Test without authentication
        self._test_auth(
            method="get_l2vpn",
            client=self.default_client,
            url=f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}",
            mock_request=mock_get,
            service_id=TEST_SERVICE_ID,
        )

    @patch("requests.get")
    def test_get_all_l2vpns_with_and_without_auth(self, mock_get):
        """Test get_all_l2vpns with and without authentication."""
        # Mock the response for retrieving all L2VPNs
        mock_get.return_value.json.return_value = MOCK_RESPONSE

        # Test retrieval of archived L2VPNs with authentication
        self._test_auth(
            method="get_all_l2vpns",
            client=self.auth_client,
            url=f"{TEST_URL}/l2vpn/1.0/archived",
            mock_request=mock_get,
            archived=True,
        )

        # Reset mock for the next call
        mock_get.reset_mock()

        # Test retrieval of active L2VPNs without authentication
        self._test_auth(
            method="get_all_l2vpns",
            client=self.default_client,
            url=f"{TEST_URL}/l2vpn/1.0",
            mock_request=mock_get,
            archived=False,
        )


@patch("requests.patch")
def test_update_l2vpn_with_and_without_auth(self, mock_patch):
    """Test update_l2vpn with and without authentication."""
    # Mock the response for the L2VPN update
    mock_response = Mock()
    mock_response.json.return_value = {"service_id": TEST_SERVICE_ID}
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    # Test with authentication
    self._test_auth(
        method="update_l2vpn",
        client=self.auth_client,
        url=f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}",
        mock_request=mock_patch,
        service_id=TEST_SERVICE_ID,
        json={"service_id": TEST_SERVICE_ID, "name": "UpdatedName",},
    )

    # Reset the mock for the next call
    mock_patch.reset_mock()

    # Test without authentication
    self._test_auth(
        method="update_l2vpn",
        client=self.default_client,
        url=f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}",
        mock_request=mock_patch,
        service_id=TEST_SERVICE_ID,
        json={
            "service_id": TEST_SERVICE_ID,
            "name": "UpdatedName",  # Optional parameter for update
        },
    )

    @patch("requests.delete")
    def test_delete_l2vpn_with_and_without_auth(self, mock_delete):
        """Test delete_l2vpn with and without authentication."""
        # Test deletion with authentication
        self._test_auth(
            method="delete_l2vpn",
            client=self.auth_client,
            url=f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}",
            mock_request=mock_delete,
            service_id=TEST_SERVICE_ID,
        )

        # Reset the mock for the next call
        mock_delete.reset_mock()

        # Test deletion without authentication
        self._test_auth(
            method="delete_l2vpn",
            client=self.default_client,
            url=f"{TEST_URL}/l2vpn/1.0/{TEST_SERVICE_ID}",
            mock_request=mock_delete,
            service_id=TEST_SERVICE_ID,
        )

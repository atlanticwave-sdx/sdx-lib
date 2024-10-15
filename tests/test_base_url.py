import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from unittest.mock import patch, Mock
from sdxlib.sdx_client import SDXClient
from sdxlib.sdx_exception import SDXException
from test_config import TEST_URL, TEST_NAME, TEST_ENDPOINTS

import unittest


class TestSDXClient(unittest.TestCase):
    def setUp(self):
        # Create an instance of SDXClient with a default valid base_url
        self.client = SDXClient(base_url=TEST_URL)

    def test_base_url_setter_valid(self):
        """Test that the base_url setter accepts a valid URL."""
        valid_url = TEST_URL
        self.client.base_url = valid_url
        self.assertEqual(self.client._base_url, valid_url)

    def test_base_url_setter_invalid_empty_string(self):
        """Test that setting an empty string raises a ValueError."""
        with self.assertRaises(ValueError) as context:
            self.client.base_url = ""
        self.assertEqual(str(context.exception), "Base URL must be a non-empty string.")

    def test_base_url_setter_invalid_whitespace_string(self):
        """Test that setting a string with only whitespace raises a ValueError."""
        with self.assertRaises(ValueError) as context:
            self.client.base_url = "   "
        self.assertEqual(str(context.exception), "Base URL must be a non-empty string.")

    def test_base_url_setter_invalid_non_string(self):
        """Test that setting a non-string value raises a ValueError."""
        with self.assertRaises(ValueError) as context:
            self.client.base_url = 12345  # Non-string value
        self.assertEqual(str(context.exception), "Base URL must be a non-empty string.")


if __name__ == "__main__":
    unittest.main()

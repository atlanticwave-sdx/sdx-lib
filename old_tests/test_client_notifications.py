import unittest
from sdxlib.sdx_client import SDXClient
from test_config import (
    create_client,
    ERROR_NOTIFICATIONS_NOT_LIST,
    ERROR_NOTIFICATION_ITEM_NOT_DICT,
    ERROR_NOTIFICATION_ITEM_EMAIL_KEY,
    ERROR_NOTIFICATION_INVALID_EMAIL_FORMAT,
    ERROR_NOTIFICATION_EXCEEDS_LIMIT,
)


class TestSDXClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = create_client()

    def assert_valid_notifications(
        self, invalid_value, expected_message, exception=ValueError
    ):
        with self.assertRaises(exception) as context:
            self.client.notifications = invalid_value
        self.assertEqual(str(context.exception), expected_message)

    def test_set_notifications_none(self):
        """Test setting notifications to None."""
        self.client.notifications = None  # Setting notifications to None
        self.assertIsNone(self.client._notifications)

    # Unit Tests for Notifications Attribute(Optional) #
    def test_notifications_valid(self):
        """Test setting and getting valid notifications within the 10-email limit."""
        valid_notifications = [
            {"email": "user1@email.com",},
            {"email": "user2@email.com",},
        ]
        self.client.notifications = valid_notifications
        self.assertEqual(self.client.notifications, valid_notifications)

    def test_notifications_not_list(self):
        """Test setting notifications with a non-list value, expecting a ValueError."""
        invalid_notifications = ({"email": "user1@email.com",},)
        self.assert_valid_notifications(
            invalid_notifications, ERROR_NOTIFICATIONS_NOT_LIST
        )

    def test_notifications_list_element_not_dict(self):
        """Test setting notifications with a non-dictionary entry, expecting a ValueError."""
        invalid_notifications = [
            {"email": "user1@email.com",},
            "not a dict",
        ]
        self.assert_valid_notifications(
            invalid_notifications, ERROR_NOTIFICATION_ITEM_NOT_DICT
        )

    def test_notifications_dict_no_email_key(self):
        """Test setting notification with a dictionary missing the 'email' key, expecting a ValueError."""
        invalid_notifications = [
            {"email": "user1@email.com",},
            {"not_email": "user2@email.com",},
        ]
        self.assert_valid_notifications(
            invalid_notifications, ERROR_NOTIFICATION_ITEM_EMAIL_KEY
        )

    def test_notifications_dict_non_valid_email(self):
        """Test setting notifications with an invalid email format, expecting a ValueError."""
        invalid_notifications = [
            {"email": "user1@email.com",},
            {"email": "invalid_email",},
        ]
        self.assert_valid_notifications(
            invalid_notifications, ERROR_NOTIFICATION_INVALID_EMAIL_FORMAT
        )

    def test_notifications_list_too_long(self):
        """Test setting notifications exceeding 10-email limit, expecting a ValueError."""
        exceeding_notifications = [{"email": f"user{i}@email.com"} for i in range(11)]
        self.assert_valid_notifications(
            exceeding_notifications, ERROR_NOTIFICATION_EXCEEDS_LIMIT
        )

    def test_email_validation_non_string(self):
        """Test with non-string inputs, expecting False."""
        non_string_inputs = [None, 123, 45.67, [], {}, set(), object()]

        for input_value in non_string_inputs:
            self.assertFalse(SDXClient.is_valid_email(input_value))

    def test_email_validation_empty_string(self):
        """Test with an empty string input, expecting False."""
        self.assertFalse(SDXClient.is_valid_email(""))

    def test_email_validation_valid(self):
        """Test with valid email format."""
        self.assertTrue(SDXClient.is_valid_email("test@example.com"))

    def test_email_validation_invalid_format(self):
        """Test with an invalid email format (missing '@')."""
        self.assertFalse(SDXClient.is_valid_email("invalid-email.com"))


# Run the tests
if __name__ == "__main__":
    unittest.main()

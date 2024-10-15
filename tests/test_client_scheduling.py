import unittest
from sdxlib.sdx_client import SDXClient
from test_config import (
    create_client,
    ERROR_SCHEDULING_FORMAT,
    ERROR_SCHEDULING_END_BEFORE_START,
    ERROR_SCHEDULING_NOT_DICT,
)


class TestSDXClientScheduling(unittest.TestCase):
    def setUp(self) -> None:
        self.client = create_client(scheduling=None)

    def assert_invalid_scheduling(
        self, invalid_value, expected_message, exception=ValueError
    ):
        with self.assertRaises(exception) as context:
            self.client.scheduling = invalid_value
        self.assertEqual(str(context.exception), expected_message)

    def test_valid_scheduling_both_times(self):
        """Tests valid scheduling with both start and end times."""
        client_scheduling = {
            "start_time": "2024-07-04T10:00:00Z",
            "end_time": "2024-07-05T18:00:00Z",
        }
        self.client.scheduling = client_scheduling
        self.assertEqual(
            self.client.scheduling, client_scheduling,
        )

    def test_set_scheduling_to_none(self):
        """Tests setting scheduling to None."""
        self.client.scheduling = None  # Set to None
        self.assertIsNone(self.client.scheduling)

    def test_invalid_scheduling_not_dict(self):
        """Tests invalid scheduling data type (not a dictionary)."""
        invalid_scheduling = "not a dictionary"
        self.assert_invalid_scheduling(
            invalid_scheduling, "Scheduling attribute must be a dictionary.", TypeError
        )

    def test_invalid_scheduling_invalid_key(self):
        """Tests scheduling with an invalid key."""
        invalid_scheduling = {"invalid_key": "2024-07-04T10:00:00Z"}
        self.assert_invalid_scheduling(
            invalid_scheduling, "Invalid scheduling key: invalid_key"
        )

    def test_invalid_scheduling_non_string_value(self):
        """Tests scheduling with non-string values."""
        invalid_scheduling = {
            "start_time": 12345,  # Non-string value
            "end_time": "2024-07-05T18:00:00Z",
        }
        self.assert_invalid_scheduling(
            invalid_scheduling, "start_time must be a string.", TypeError
        )

    def test_valid_scheduling_end_time_only(self):
        """Tests valid scheduling with only end time provided."""
        client_scheduling = {"end_time": "2024-07-05T18:00:00Z"}
        self.client.scheduling = client_scheduling
        self.assertEqual(self.client.scheduling, client_scheduling)

    def test_valid_scheduling_empty_dict(self):
        """Tests valid scheduling with an empty dictionary."""
        self.client.scheduling = {}
        self.assertEqual(self.client.scheduling, None)

    def test_invalid_scheduling_format(self):
        """Tests invalid scheduling format for start_time."""
        invalid_scheduling = {"start_time": "invalid format"}
        self.assert_invalid_scheduling(
            invalid_scheduling, ERROR_SCHEDULING_FORMAT,
        )

    def test_invalid_scheduling_end_before_start(self):
        """Tests invalid scheduling where end_time is before start_time."""
        invalid_scheduling = {
            "start_time": "2024-07-05T18:00:00Z",
            "end_time": "2024-07-05T10:00:00Z",
        }
        self.assert_invalid_scheduling(
            invalid_scheduling, ERROR_SCHEDULING_END_BEFORE_START
        )


if __name__ == "__main__":
    unittest.main()

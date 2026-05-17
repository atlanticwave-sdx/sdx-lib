import unittest
from sdxlib.sdx_client import SDXClient
from test_config import TEST_URL


class TestSDXClient(unittest.TestCase):
    def setUp(self):
        # Create an instance of SDXClient or Mock it if required
        self.client = SDXClient(base_url=TEST_URL)
        self.valid_keys = ["min_bw", "max_delay", "max_number_oxps"]

    def test_qos_metrics_none(self):
        """Test setting qos_metrics to None"""
        self.assertIsNone(self.client.qos_metrics)

    def test_validate_qos_metrics_none(self):
        """Test that when qos_metrics is None, the function returns without errors."""
        result = self.client._validate_qos_metric(qos_metrics=None)
        self.assertIsNone(result)

    def test_qos_metrics_invalid_key(self):
        """Test that ValueError is raised for invalid QoS metric key."""
        invalid_qos_metrics = {
            "invalid_key": {"value": 10}  # Invalid key not in valid_keys
        }

        with self.assertRaises(ValueError) as context:
            self.client._validate_qos_metric(qos_metrics=invalid_qos_metrics)

        self.assertEqual(str(context.exception), "Invalid QoS metric: invalid_key")

    def test_qos_metrics_value_not_dict(self):
        """Test that TypeError is raised when QoS metric value is not a dictionary."""
        invalid_qos_metrics = {
            "min_bw": 10  # Invalid: value should be a dictionary, not an integer
        }

        with self.assertRaises(TypeError) as context:
            self.client._validate_qos_metric(qos_metrics=invalid_qos_metrics)

        self.assertEqual(
            str(context.exception),
            "QoS metric value for 'min_bw' must be a dictionary.",
        )

    def test_missing_value_key_in_qos_metric(self):
        """Test that missing 'value' key in QoS metric raises a ValueError."""
        invalid_value_dict = {"strict": True}  # Missing "value" key
        with self.assertRaises(ValueError) as context:
            self.client._validate_qos_metric_value("min_bw", invalid_value_dict)
        self.assertEqual(
            str(context.exception),
            "Missing required key 'value' in QoS metric for 'min_bw'",
        )

    def test_value_key_not_integer(self):
        """Test that non-integer 'value' in QoS metric raises a TypeError."""
        invalid_value_dict = {
            "value": "not_an_integer",
            "strict": True,
        }  # "value" is a string, should be an int
        with self.assertRaises(TypeError) as context:
            self.client._validate_qos_metric_value("min_bw", invalid_value_dict)
        self.assertEqual(
            str(context.exception),
            "QoS value for '{key}' must be an integer.".format(key="min_bw"),
        )

    def test_strict_key_not_boolean(self):
        """Test that non-boolean 'strict' key in QoS metric raises a TypeError."""
        invalid_value_dict = {
            "value": 10,
            "strict": "not_a_boolean",
        }  # "strict" is a string, should be a bool
        with self.assertRaises(TypeError) as context:
            self.client._validate_qos_metric_value("min_bw", invalid_value_dict)
        self.assertEqual(
            str(context.exception),
            "'strict' in QoS metric of 'min_bw' must be a boolean.",
        )

    def assert_invalid_qos_metrics(
        self, invalid_value, expected_message, exception=ValueError
    ):
        with self.assertRaises(exception) as context:
            self.client.qos_metrics = invalid_value
        self.assertEqual(str(context.exception), expected_message)

    def test_qos_metrics_empty_dict(self):
        """Test setting qos_metrics to an empty dictionary"""
        self.client.qos_metrics = {}
        self.assertIsNone(self.client.qos_metrics)

    def test_qos_metrics_valid(self):
        """Test setting qos_metrics with valid data"""
        client_qos_metrics = {
            "min_bw": {"value": 10, "strict": False},
            "max_delay": {"value": 200, "strict": True},
        }
        self.client.qos_metrics = client_qos_metrics
        self.assertEqual(self.client.qos_metrics, client_qos_metrics)

    def test_qos_metrics_invalid_type(self):
        """Test setting qos_metrics with invalid type"""
        invalid_value = "invalid string"
        self.assert_invalid_qos_metrics(
            invalid_value, "QoS metrics must be a dictionary.", TypeError
        )

    def test_qos_metrics_min_bw_out_of_range(self):
        """Test setting min_bw with value outside valid range"""
        invalid_value = {"min_bw": {"value": -10, "strict": False}}
        self.assert_invalid_qos_metrics(
            invalid_value, "qos_metric 'min_bw' value must be between 0 and 100."
        )

    def test_validate_qos_metric_max_delay_invalid(self):
        """Test that an out-of-range value for max_delay raises a ValueError."""
        invalid_value_dict = {"value": 1500}  # Out of range (0-1000)
        with self.assertRaises(ValueError) as context:
            self.client._validate_qos_metric_value("max_delay", invalid_value_dict)
        self.assertEqual(
            str(context.exception),
            "qos_metric 'max_delay' value must be between 0 and 1000.",
        )

    def test_validate_qos_metric_max_number_oxps_invalid(self):
        """Test that an out-of-range value for max_number_oxps raises a ValueError."""
        invalid_value_dict = {"value": 150}  # Out of range (1-100)
        with self.assertRaises(ValueError) as context:
            self.client._validate_qos_metric_value(
                "max_number_oxps", invalid_value_dict
            )
        self.assertEqual(
            str(context.exception),
            "qos_metric 'max_number_oxps' value must be between 1 and 100.",
        )


# Run the tests
if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch
from sdxlib.sdx_client import SDXClient


class TestSDXClientStringRepresentation(unittest.TestCase):
    def test_str_method(self):
        """Test the string output of the SDXClient.__str__ method."""
        client = SDXClient(
            base_url="http://fake-api-url.com",
            name="TestClient",
            endpoints=[{"type": "endpoint1"}, {"type": "endpoint2"}],
            description="Test description",
            notifications=[{"email": "test@example.com"}],
            scheduling={
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T12:00:00",
            },
            qos_metrics={"metric1": {"threshold": 5, "enabled": True}},
        )

        expected_str = (
            "SDXClient(name=TestClient, endpoints=[{'type': 'endpoint1'}, {'type': 'endpoint2'}], "
            "description=Test description, notifications=[{'email': 'test@example.com'}], "
            "scheduling={'start_time': '2024-01-01T10:00:00', 'end_time': '2024-01-01T12:00:00'}, "
            "qos_metrics={'metric1': {'threshold': 5, 'enabled': True}}, base url=http://fake-api-url.com"
        )

        self.assertEqual(str(client), expected_str)

    def test_repr_method(self):
        """Test the string output of the SDXClient.__repr__ method."""
        client = SDXClient(
            base_url="http://fake-api-url.com",
            name="TestClient",
            endpoints=[{"type": "endpoint1"}, {"type": "endpoint2"}],
            description="Test description",
            notifications=[{"email": "test@example.com"}],
            scheduling={
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T12:00:00",
            },
            qos_metrics={"metric1": {"threshold": 5, "enabled": True}},
        )

        expected_repr = (
            "SDXClient(name=TestClient, endpoints=[{'type': 'endpoint1'}, {'type': 'endpoint2'}], "
            "description=Test description, notifications=[{'email': 'test@example.com'}], "
            "scheduling={'start_time': '2024-01-01T10:00:00', 'end_time': '2024-01-01T12:00:00'}, "
            "qos_metrics={'metric1': {'threshold': 5, 'enabled': True}}, base url=http://fake-api-url.com"
        )

        self.assertEqual(repr(client), expected_repr)


if __name__ == "__main__":
    unittest.main()

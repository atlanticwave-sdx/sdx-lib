import unittest
from unittest.mock import patch
from sdxlib.sdx_client import SDXClient


class TestSDXClientStringRepresentation(unittest.TestCase):
    def test_str_method(self):
        """Test the string output of the SDXClient.__str__ method."""
        self.maxDiff = None
        client = SDXClient(
            base_url="http://fake-api-url.com",
            name="TestClient",
            endpoints=[
                {
                    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name",
                    "vlan": "100",
                },
                {
                    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name2",
                    "vlan": "200",
                },
            ],
            description="Test description",
            notifications=[{"email": "test@example.com"}],
            scheduling={
                "start_time": "2024-07-04T10:00:00Z",
                "end_time": "2024-07-05T18:00:00Z",
            },
            qos_metrics={
                "min_bw": {"value": 10, "strict": False},
                "max_delay": {"value": 200, "strict": True},
            },
        )

        expected_str = (
            "SDXClient(name=TestClient, "
            "endpoints=[{'port_id': 'urn:sdx:port:test-oxp_url:test-node_name:test-port_name', 'vlan': '100'}, "
            "{'port_id': 'urn:sdx:port:test-oxp_url:test-node_name:test-port_name2', 'vlan': '200'}], "
            "description=Test description, "
            "notifications=[{'email': 'test@example.com'}], "
            "scheduling={'start_time': '2024-07-04T10:00:00Z', 'end_time': '2024-07-05T18:00:00Z'}, "
            "qos_metrics={'min_bw': {'value': 10, 'strict': False}, 'max_delay': {'value': 200, 'strict': True}}, "
            "base_url=http://fake-api-url.com)"
        )

        self.assertEqual(str(client), expected_str)

    def test_repr_method(self):
        """Test the string output of the SDXClient.__repr__ method."""
        client = SDXClient(
            base_url="http://fake-api-url.com",
            name="TestClient",
            endpoints=[
                {
                    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name",
                    "vlan": "100",
                },
                {
                    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name2",
                    "vlan": "200",
                },
            ],
            description="Test description",
            notifications=[{"email": "test@example.com"}],
            scheduling={
                "start_time": "2024-07-04T10:00:00Z",
                "end_time": "2024-07-05T18:00:00Z",
            },
            qos_metrics={
                "min_bw": {"value": 10, "strict": False},
                "max_delay": {"value": 200, "strict": True},
            },
        )

        expected_repr = (
            "SDXClient(name=TestClient, "
            "endpoints=[{'port_id': 'urn:sdx:port:test-oxp_url:test-node_name:test-port_name', 'vlan': '100'}, "
            "{'port_id': 'urn:sdx:port:test-oxp_url:test-node_name:test-port_name2', 'vlan': '200'}], "
            "description=Test description, "
            "notifications=[{'email': 'test@example.com'}], "
            "scheduling={'start_time': '2024-07-04T10:00:00Z', 'end_time': '2024-07-05T18:00:00Z'}, "
            "qos_metrics={'min_bw': {'value': 10, 'strict': False}, 'max_delay': {'value': 200, 'strict': True}}, "
            "base_url=http://fake-api-url.com)"
        )

        self.assertEqual(repr(client), expected_repr)


if __name__ == "__main__":
    unittest.main()

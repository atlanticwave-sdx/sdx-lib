import json
import unittest
from sdxlib.sdx_client import SDXClient
from sdxlib.sdx_topology import Topology
from topology_test_config import (
    valid_topology,
    invalid_topology_empty_nodes,
    invalid_topology_bad_id,
    MOCK_TOPOLOGY,
)
from test_config import TEST_URL
from unittest.mock import patch


class TestTopology(unittest.TestCase):
    def test_valid_topology(self):
        """Test that a valid topology object is created successfully"""
        topology = Topology(**valid_topology)
        self.assertEqual(topology.name, "Test-Topology")
        self.assertEqual(topology.id, "urn:sdx:topology:amlight.net")
        self.assertEqual(topology.version, 1)
        self.assertEqual(len(topology.nodes), 2)

    def test_invalid_empty_nodes(self):
        """Test that an empty nodes list raises a ValueError"""
        with self.assertRaises(ValueError):
            Topology(**invalid_topology_empty_nodes)

    def test_invalid_topology_id(self):
        """Test that an invalid ID format raises a ValueError"""
        with self.assertRaises(ValueError):
            Topology(**invalid_topology_bad_id)

    @patch("sdxlib.sdx_client.requests.get")
    def test_get_topology(self, mock_get):
        """Mock get_topology to return test topology."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_TOPOLOGY

        client = SDXClient(base_url=TEST_URL)
        topology = client.get_topology()

        assert topology.name == "Ampath-OXP"
        assert len(topology.nodes) == 1
        assert topology.nodes[0].name == "Ampath3"
        assert topology.nodes[0].ports[0].id == "urn:sdx:port:ampath.net:Ampath3:50"


if __name__ == "__main__":
    unittest.main()

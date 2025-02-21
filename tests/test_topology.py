import unittest
from sdxlib.sdx_topology import Topology
from topology_test_config import (
    valid_topology,
    invalid_topology_empty_nodes,
    invalid_topology_bad_id,
)


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


if __name__ == "__main__":
    unittest.main()

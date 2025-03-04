import json
import unittest
from sdxlib.sdx_response import SDXTopologyResponse
from sdxlib.sdx_topology import Node, Link, Port, Status, Topology
from topology_test_config import MOCK_TOPOLOGY
from dacite import from_dict, Config
from dacite.exceptions import MissingValueError


class TestSDXTopologyResponse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure that the SDXTopologyResponse object is initialized once for all tests."""
        raw_response = SDXTopologyResponse.from_json(MOCK_TOPOLOGY)
        cls.response = Topology.from_dict(raw_response.__dict__)

    def test_from_json_valid_data(self):
        """Test that SDXTopologyResponse correctly parses a valid topology JSON and converts it to Topology."""
        raw_response = SDXTopologyResponse.from_json(MOCK_TOPOLOGY)
        topology = Topology.from_dict(raw_response.__dict__)  # Convert to Topology

        self.assertEqual(len(topology.nodes), len(MOCK_TOPOLOGY["nodes"]))
        self.assertEqual(len(topology.links), len(MOCK_TOPOLOGY["links"]))

        for node in topology.nodes:
            self.assertIsInstance(node, Node)
        for link in topology.links:
            self.assertIsInstance(link, Link)
        for (
            port
        ) in (
            topology.port_lookup.values()
        ):  # Now testing Topology, not SDXTopologyResponse
            self.assertIsInstance(port, Port)

    def test_from_json_empty_data(self):
        """Test SDXTopologyResponse with an empty JSON response (should raise an error)."""
        with self.assertRaises(MissingValueError):
            SDXTopologyResponse.from_json({})

    def test_from_json_missing_nodes(self):
        """Test SDXTopologyResponse with missing 'nodes' key in JSON response."""
        response = SDXTopologyResponse.from_json(
            {
                "name": MOCK_TOPOLOGY["name"],
                "id": MOCK_TOPOLOGY["id"],
                "version": MOCK_TOPOLOGY["version"],
                "timestamp": MOCK_TOPOLOGY["timestamp"],
                "model_version": MOCK_TOPOLOGY["model_version"],
                "links": MOCK_TOPOLOGY["links"],  # Keep links but remove nodes
            }
        )
        self.assertEqual(len(response.nodes), 0)  # Nodes should be empty but not fail
        self.assertEqual(len(response.links), len(MOCK_TOPOLOGY["links"]))

    def test_from_json_missing_links(self):
        """Test SDXTopologyResponse with missing 'links' key in JSON response."""
        response = SDXTopologyResponse.from_json(
            {
                "name": MOCK_TOPOLOGY["name"],
                "id": MOCK_TOPOLOGY["id"],
                "version": MOCK_TOPOLOGY["version"],
                "timestamp": MOCK_TOPOLOGY["timestamp"],
                "model_version": MOCK_TOPOLOGY["model_version"],
                "nodes": MOCK_TOPOLOGY["nodes"],  # Keep nodes but remove links
            }
        )
        self.assertEqual(len(response.nodes), len(MOCK_TOPOLOGY["nodes"]))
        self.assertEqual(len(response.links), 0)

    def test_from_json_invalid_node_data(self):
        """Test SDXTopologyResponse with invalid node data format."""
        invalid_data = {
            "nodes": [{"id": "urn:sdx:node:invalid", "ports": []}],  # Missing "name"
            "links": MOCK_TOPOLOGY["links"],
        }
        with self.assertRaises(MissingValueError):
            SDXTopologyResponse.from_json(invalid_data)

    def test_from_json_invalid_link_data(self):
        """Test SDXTopologyResponse with invalid link data format."""
        invalid_data = {
            "nodes": MOCK_TOPOLOGY["nodes"],
            "links": [{"id": "urn:sdx:link:invalid", "ports": []}],  # Missing "name"
        }
        with self.assertRaises(MissingValueError):
            SDXTopologyResponse.from_json(invalid_data)

    def test_get_available_ports(self):
        """Test retrieving available ports that are UP and not NNI."""
        available_ports = self.response.get_available_ports()
        for port in available_ports:
            self.assertEqual(port.status, Status.UP)
            self.assertFalse(port.nni)  # Ensure it's not an NNI port

    def test_search_ports_found(self):
        """Test searching for ports by substring in the port name."""
        search_term = "eth"
        results = self.response.search_ports(search_term)
        self.assertGreater(len(results), 0)
        for port in results:
            self.assertIn(search_term.lower(), port.name.lower())

    def test_search_ports_not_found(self):
        """Test searching for a non-existent port name substring."""
        search_term = "nonexistent"
        results = self.response.search_ports(search_term)
        self.assertEqual(len(results), 0)

    def test_search_entities_found(self):
        """Test searching for ports based on entity names."""
        search_term = "University"
        results = self.response.search_entities(search_term)
        self.assertGreater(len(results), 0)
        for port in results:
            self.assertTrue(
                any(search_term.lower() in entity.lower() for entity in port.entities)
            )

    def test_search_entities_not_found(self):
        """Test searching for a non-existent entity."""
        search_term = "Google"
        results = self.response.search_entities(search_term)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()

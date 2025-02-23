import json
import unittest
from sdxlib.sdx_response import SDXTopologyResponse
from sdxlib.sdx_topology import Node, Link, Port, Status, State
from topology_test_config import MOCK_TOPOLOGY
from dacite import from_dict, Config
from dacite.exceptions import MissingValueError

class TestSDXTopologyResponse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure that the SDXTopologyResponse object is initialized once for all tests."""
        cls.response = SDXTopologyResponse.from_json(MOCK_TOPOLOGY)
    
    def test_from_json_valid_data(self):
        """Test that SDXTopologyResponse correctly parses a valid topology JSON."""
        response = SDXTopologyResponse.from_json(MOCK_TOPOLOGY)
        self.assertEqual(len(response.nodes), len(MOCK_TOPOLOGY["nodes"]))
        self.assertEqual(len(response.links), len(MOCK_TOPOLOGY["links"]))
        for node in response.nodes:
            self.assertIsInstance(node, Node)
        for link in response.links:
            self.assertIsInstance(link, Link)
        for port in response.port_lookup.values():
            self.assertIsInstance(port, Port)
    
    def test_from_json_empty_data(self):
        """Test SDXTopologyResponse with an empty JSON response."""
        response = SDXTopologyResponse.from_json({})
        self.assertEqual(len(response.nodes), 0)
        self.assertEqual(len(response.links), 0)
        self.assertEqual(len(response.port_lookup), 0)
    
    def test_from_json_missing_nodes(self):
        """Test SDXTopologyResponse with missing 'nodes' key in JSON response."""
        response = SDXTopologyResponse.from_json({"links": MOCK_TOPOLOGY["links"]})
        self.assertEqual(len(response.nodes), 0)
        self.assertEqual(len(response.links), len(MOCK_TOPOLOGY["links"]))
    
    def test_from_json_missing_links(self):
        """Test SDXTopologyResponse with missing 'links' key in JSON response."""
        response = SDXTopologyResponse.from_json({"nodes": MOCK_TOPOLOGY["nodes"]})
        self.assertEqual(len(response.nodes), len(MOCK_TOPOLOGY["nodes"]))
        self.assertEqual(len(response.links), 0)
    
    def test_from_json_invalid_node_data(self):
        """Test SDXTopologyResponse with invalid node data format."""
        invalid_data = {
            "nodes": [{"id": "urn:sdx:node:invalid", "ports": []}],  # Missing "name"
            "links": MOCK_TOPOLOGY["links"]
        }
        with self.assertRaises(MissingValueError):
            SDXTopologyResponse.from_json(invalid_data)
    
    def test_from_json_invalid_link_data(self):
        """Test SDXTopologyResponse with invalid link data format."""
        invalid_data = {
            "nodes": MOCK_TOPOLOGY["nodes"],
            "links": [{"id": "urn:sdx:link:invalid", "ports": []}]  # Missing "name"
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
            self.assertTrue(any(search_term.lower() in entity.lower() for entity in port.entities))
    
    def test_search_entities_not_found(self):
        """Test searching for a non-existent entity."""
        search_term = "Google"
        results = self.response.search_entities(search_term)
        self.assertEqual(len(results), 0) 
    
if __name__ == "__main__":
    unittest.main()

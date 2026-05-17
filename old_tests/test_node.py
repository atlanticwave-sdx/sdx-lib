import unittest
from sdxlib.sdx_topology import Node, Status, State
from topology_test_config import sample_node1


class TestNode(unittest.TestCase):
    def test_valid_node(self):
        """Test that a valid Node object is created successfully."""
        node = sample_node1
        self.assertEqual(node.name, "switch01")
        self.assertEqual(node.id, "urn:sdx:node:amlight.net:switch01")
        self.assertEqual(len(node.ports), 1)
        self.assertEqual(node.status, Status.UP)
        self.assertEqual(node.state, State.ENABLED)

    def test_invalid_node_name_too_long(self):
        """Test that a Node with a name longer than 30 characters raises ValueError."""
        with self.assertRaises(ValueError):
            Node(
                name="a" * 31,  # Too many characters
                id=sample_node1.id,
                location=sample_node1.location,
                ports=sample_node1.ports,
                status=sample_node1.status,
                state=sample_node1.state,
            )

    def test_invalid_node_name_special_chars(self):
        """Test that a Node with an invalid name (wrong characters) raises ValueError."""
        with self.assertRaises(ValueError):
            Node(
                name="Invalid@Node!",
                id=sample_node1.id,
                location=sample_node1.location,
                ports=sample_node1.ports,
                status=sample_node1.status,
                state=sample_node1.state,
            )

    def test_invalid_node_id_format(self):
        """Test that a Node with an invalid ID format raises ValueError."""
        with self.assertRaises(ValueError):
            Node(
                name=sample_node1.name,
                id="invalid-id-format",  # Wrong format
                location=sample_node1.location,
                ports=sample_node1.ports,
                status=sample_node1.status,
                state=sample_node1.state,
            )

    def test_node_without_ports(self):
        """Test that a Node with an empty ports list raises ValueError."""
        with self.assertRaises(ValueError):
            Node(
                name=sample_node1.name,
                id=sample_node1.id,
                location=sample_node1.location,
                ports=[],  # No ports
                status=sample_node1.status,
                state=sample_node1.state,
            )

    def test_invalid_ports_type(self):
        """Test that a Node with a non-Port object in the ports list raises TypeError."""
        with self.assertRaises(TypeError):
            Node(
                name=sample_node1.name,
                id=sample_node1.id,
                location=sample_node1.location,
                ports=["not-a-port"],  # String instead of a Port object
                status=sample_node1.status,
                state=sample_node1.state,
            )

    def test_node_with_none_ports(self):
        """Test that a Node with None as ports raises TypeError."""
        with self.assertRaises(ValueError):
            Node(
                name=sample_node1.name,
                id=sample_node1.id,
                location=sample_node1.location,
                ports=None,  # Ports set to None
                status=sample_node1.status,
                state=sample_node1.state,
            )


if __name__ == "__main__":
    unittest.main()

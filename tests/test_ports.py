import unittest
from sdxlib.sdx_topology import Port, Status, State, PortType
from topology_test_config import (
    sample_port1,
    sample_port2,
    invalid_port_long_name,
    invalid_port_special_chars,
    invalid_port_bad_id,
    invalid_port_mtu_low,
    invalid_port_mtu_high,
)


class TestPort(unittest.TestCase):
    def test_valid_port(self):
        """Test that a valid Port object is created successfully."""
        port = sample_port1
        self.assertEqual(port.name, "Port1")
        self.assertEqual(port.id, "urn:sdx:port:amlight.net:Node1:Port1")
        self.assertEqual(port.node, "urn:sdx:node:amlight.net:Node1")
        self.assertEqual(port.type, PortType.GE_10)
        self.assertEqual(port.status, Status.UP)
        self.assertEqual(port.state, State.ENABLED)

    def test_invalid_port_name_too_long(self):
        """Test that a Port with a name longer than 30 characters raises ValueError."""
        with self.assertRaises(ValueError):
            Port(**invalid_port_long_name)

    def test_invalid_port_name_special_chars(self):
        """Test that a Port with an invalid name containing unsupported characters raises ValueError."""
        with self.assertRaises(ValueError):
            Port(**invalid_port_special_chars)

    def test_invalid_port_id_format(self):
        """Test that a Port with an invalid ID format raises ValueError."""
        with self.assertRaises(ValueError):
            Port(**invalid_port_bad_id)

    def test_invalid_mtu_too_low(self):
        """Test that a Port with an MTU below 1500 raises ValueError."""
        with self.assertRaises(ValueError):
            Port(**invalid_port_mtu_low)

    def test_invalid_mtu_too_high(self):
        """Test that a Port with an MTU above 10000 raises ValueError."""
        with self.assertRaises(ValueError):
            Port(**invalid_port_mtu_high)

    def test_valid_port_with_entities(self):
        """Test that a Port with valid entities is created successfully."""
        port = sample_port2
        self.assertEqual(port.entities, ["Sprace", "UNESP", "LHC Tier 2 Brazil"])


if __name__ == "__main__":
    unittest.main()

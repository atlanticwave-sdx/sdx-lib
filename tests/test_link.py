import unittest
from sdxlib.sdx_topology import Link, Status, State
from topology_test_config import sample_link, sample_port1, sample_port2


class TestLink(unittest.TestCase):
    def test_valid_link(self):
        """Test that a valid_Link object is created successfully using predefined variable."""
        link = sample_link
        self.assertEqual(link.name, "100G_Sao_Paulo_to_Miami")
        self.assertEqual(link.id, "urn:sdx:link:amlight.net:saopaulo_miami")
        self.assertEqual(link.ports, sample_link.ports)
        self.assertEqual(link.bandwidth, 100.0)
        self.assertEqual(link.residual_bandwidth, 50.0)
        self.assertEqual(link.latency, 10.5)
        self.assertEqual(link.packet_loss, 0.5)
        self.assertEqual(link.availability, 99.9)
        self.assertEqual(link.status, Status.UP)
        self.assertEqual(link.state, State.ENABLED)
        self.assertEqual(link.private, ["residual_bandwidth"])

    def test_invalid_link_name(self):
        """Test that a Link with an invalid name raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="A" * 31,  # Exceeds 30-character limit
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
            )

    def test_invalid_link_id(self):
        """Test that a Link with an invalid ID format raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="invalid-id-format",  # Incorrect format
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
            )

    def test_invalid_ports_length(self):
        """Test that a Link with an incorrect number of ports raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id],  # Only 1 port instead of 2
                bandwidth=100.0,
            )

    def test_invalid_ports_type(self):
        """Test that a Link with a non-string port ID raises TypeError."""
        with self.assertRaises(TypeError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[123, sample_port2.id],  # First port ID is an int
                bandwidth=100.0,
            )

    def test_invalid_bandwidth(self):
        """Test that a Link with a non-positive bandwidth raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=0.0,  # Must be > 0
            )

    def test_invalid_residual_bandwidth(self):
        """Test that a Link with an invalid residual_bandwidth raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
                residual_bandwidth=150.0,  # Must be between 0 and 100
            )

    def test_invalid_latency(self):
        """Test that a Link with a negative latency raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
                latency=-5.0,  # Must be non-negative
            )

    def test_invalid_packet_loss(self):
        """Test that a Link with an invalid packet_loss raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
                packet_loss=150.0,  # Must be between 0 and 100
            )

    def test_invalid_availability(self):
        """Test that a Link with an invalid availability raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
                availability=150.0,  # Must be between 0 and 100
            )

    def test_invalid_private_value(self):
        """Test that a Link with an invalid private attribute raises ValueError."""
        with self.assertRaises(ValueError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
                private=[
                    "invalid_value"
                ],  # Must be one of ["residual_bandwidth", "latency", "packet_loss"]
            )

    def test_invalid_private_type(self):
        """Test that a Link with a non-list private attribute raises TypeError."""
        with self.assertRaises(TypeError):
            Link(
                name="Valid_Link",
                id="urn:sdx:link:amlight.net:saopaulo_miami",
                ports=[sample_port1.id, sample_port2.id],
                bandwidth=100.0,
                private="residual_bandwidth",  # Should be a list, not a string
            )


if __name__ == "__main__":
    unittest.main()

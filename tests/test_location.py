import unittest
from sdxlib.sdx_topology import Location

class TestLocation(unittest.TestCase):
    
    def test_valid_location(self):
        location = Location(address="123 Main St", latitude=40.7128, longitude=-74.0060, iso3166_2_lvl4="US-NY")
        self.assertEqual(location.address, "123 Main St")
        self.assertEqual(location.latitude, 40.7128)
        self.assertEqual(location.longitude, -74.0060)
        self.assertEqual(location.iso3166_2_lvl4, "US-NY")
    
    def test_invalid_latitude(self):
        with self.assertRaises(ValueError):
            Location(address="123 Main St", latitude=100, longitude=-74.0060, iso3166_2_lvl4="US-NY")
    
    def test_invalid_longitude(self):
        with self.assertRaises(ValueError):
            Location(address="123 Main St", latitude=40.7128, longitude=-190, iso3166_2_lvl4="US-NY")
    
    def test_invalid_iso_code(self):
        with self.assertRaises(ValueError):
            Location(address="123 Main St", latitude=40.7128, longitude=-74.0060, iso3166_2_lvl4="INVALID")

    def test_invalid_address_length(self):
        """Test that a location with an address over 255 characters raises ValueError."""
        long_address = "A" * 256
        with self.assertRaises(ValueError):
            Location(address=long_address, latitude=40.7128, longitude=-74.0060, iso3166_2_lvl4="US-NY")

    def test_invalid_iso_format(self):
        """Test that an improperly formatted ISO 3166-2 code raises ValueError."""
        with self.assertRaises(ValueError):
            Location(address="123 Main St", latitude=40.7128, longitude=-74.0060, iso3166_2_lvl4="USNY")

    def test_non_existent_country_code(self):
        """Test that a non-existent country code raises ValueError."""
        with self.assertRaises(ValueError):
            Location(address="123 Main St", latitude=40.7128, longitude=-74.0060, iso3166_2_lvl4="XX-NY")

if __name__ == "__main__":
    unittest.main()

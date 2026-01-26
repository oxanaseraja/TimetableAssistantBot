"""
Tests for timezone extraction.
Specification: TIMEZONE_EXTRACTION_RULES.md
"""
import sys
import unittest
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.timezone.extractor import extract_timezone_hint, normalize_offset, tokenize


class TestTimezoneExtractor(unittest.TestCase):
    """Test timezone extraction rules."""
    
    def test_utc_offset_extraction(self):
        """Test UTC/GMT offset extraction."""
        city_index = {}
        result = extract_timezone_hint("Meeting at 10:30 UTC+2", 11, city_index)
        self.assertEqual(result, "+02:00")
        
        result = extract_timezone_hint("Call at 2pm GMT-5", 8, city_index)
        self.assertEqual(result, "-05:00")
    
    def test_iana_timezone_extraction(self):
        """Test IANA timezone ID extraction."""
        city_index = {}
        result = extract_timezone_hint("Meeting at 10:30 Europe/Amsterdam", 11, city_index)
        self.assertEqual(result, "Europe/Amsterdam")
    
    def test_city_extraction(self):
        """Test city name extraction."""
        city_index = {"amsterdam": "Europe/Amsterdam", "nyc": "America/New_York"}
        result = extract_timezone_hint("Meeting in Amsterdam at 10:30", 20, city_index)
        self.assertEqual(result, "Europe/Amsterdam")
    
    def test_offset_normalization(self):
        """Test offset normalization."""
        self.assertEqual(normalize_offset("+3"), "+03:00")
        self.assertEqual(normalize_offset("UTC+2"), "+02:00")
        self.assertEqual(normalize_offset("GMT-5"), "-05:00")
        self.assertEqual(normalize_offset("+0300"), "+03:00")
        self.assertEqual(normalize_offset("-05:30"), "-05:30")
    
    def test_tokenize(self):
        """Test text tokenization."""
        tokens = tokenize("Meeting in Amsterdam at 10:30")
        self.assertIn("Meeting", tokens)
        self.assertIn("Amsterdam", tokens)
        self.assertIn("10", tokens)
        self.assertIn("30", tokens)
    
    def test_no_timezone_found(self):
        """Test when no timezone hint is found."""
        city_index = {}
        result = extract_timezone_hint("Meeting at 10:30", 11, city_index)
        self.assertIsNone(result)
    
    def test_multiple_offsets_equal_distance(self):
        """Test that when multiple offsets are at equal distance, first by text order is selected."""
        city_index = {}
        # Two offsets at equal distance from time position (11)
        # "+02:00" at position 10, "-05:00" at position 20
        # Distance from time (position 11): |10-11|=1, |20-11|=9
        # So "+02:00" should be selected (closer)
        result = extract_timezone_hint("Meeting UTC+2 at 10:30 UTC-5", 11, city_index)
        self.assertEqual(result, "+02:00")
    
    def test_multiple_offsets_exactly_equal_distance(self):
        """Test edge case: multiple offsets at exactly equal distance from time position.
        
        Specification: TIMEZONE_EXTRACTION_RULES.md §4 - when distances are equal,
        select first by text order (left-to-right).
        """
        city_index = {}
        # Create text where both offsets are at equal distance from time
        # "UTC+2" at start, "UTC-5" at end, time in middle
        # Time "10:30" is at position 20
        # "UTC+2" starts at position 0 (distance 20)
        # "UTC-5" starts at position 40 (distance 20)
        # Both are at equal distance, should select UTC+2 (first by text order)
        text = "UTC+2 meeting at 10:30 UTC-5"
        time_pos = text.find("10:30")  # Find actual position of "10:30"
        result = extract_timezone_hint(text, time_pos, city_index)
        self.assertEqual(result, "+02:00", 
                        "When distances are equal, first match by text order (left-to-right) should be selected")
    
    def test_multiple_cities_equal_distance(self):
        """Test that when multiple cities are at equal distance, first by text order is selected."""
        city_index = {
            "amsterdam": "Europe/Amsterdam",
            "paris": "Europe/Paris"
        }
        # "Amsterdam" at position 9, "Paris" at position 20
        # Time at position 11, distances: |9-11|=2, |20-11|=9
        # So "Amsterdam" should be selected (closer)
        result = extract_timezone_hint("Meeting Amsterdam at 10:30 Paris", 11, city_index)
        self.assertEqual(result, "Europe/Amsterdam")
    
    def test_multiple_cities_exactly_equal_distance(self):
        """Test edge case: multiple cities at exactly equal distance from time position.
        
        Specification: TIMEZONE_EXTRACTION_RULES.md §4 - when distances are equal,
        select first by text order (left-to-right).
        """
        city_index = {
            "amsterdam": "Europe/Amsterdam",
            "paris": "Europe/Paris"
        }
        # Create text where both cities are at equal distance from time
        text = "Amsterdam meeting at 10:30 Paris"
        time_pos = text.find("10:30")  # Find actual position of "10:30"
        result = extract_timezone_hint(text, time_pos, city_index)
        self.assertEqual(result, "Europe/Amsterdam",
                        "When distances are equal, first match by text order (left-to-right) should be selected")
    
    def test_multiple_iana_timezones_equal_distance(self):
        """Test edge case: multiple IANA timezones at exactly equal distance.
        
        Specification: TIMEZONE_EXTRACTION_RULES.md §4 - when distances are equal,
        select first by text order (left-to-right).
        """
        city_index = {}
        # Create text where both IANA timezones are at equal distance from time
        text = "Europe/Amsterdam meeting at 10:30 Asia/Yerevan"
        time_pos = text.find("10:30")  # Find actual position of "10:30"
        result = extract_timezone_hint(text, time_pos, city_index)
        self.assertEqual(result, "Europe/Amsterdam",
                        "When distances are equal, first match by text order (left-to-right) should be selected")


if __name__ == '__main__':
    unittest.main()

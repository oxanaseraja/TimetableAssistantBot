"""
Tests for time parser.
Specification: TIME_PARSING_RULES.md
"""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.parser.time_parser import parse_times
from core.contracts import DetectedTime


class TestTimeParser(unittest.TestCase):
    """Test time parsing rules."""
    
    def test_time_24h_format(self):
        """Test 24-hour format parsing."""
        result = parse_times("Meeting at 10:30")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].hour, 10)
        self.assertEqual(result[0].minute, 30)
        self.assertIsNone(result[0].am_pm)
        self.assertFalse(result[0].ambiguous)
    
    def test_time_12h_ampm_format(self):
        """Test 12-hour format with AM/PM."""
        result = parse_times("Call at 2pm")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].hour, 2)
        self.assertIsNone(result[0].minute)
        self.assertEqual(result[0].am_pm, "PM")
        self.assertFalse(result[0].ambiguous)
        
        result = parse_times("Meeting at 10:30am")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].hour, 10)
        self.assertEqual(result[0].minute, 30)
        self.assertEqual(result[0].am_pm, "AM")
    
    def test_bare_hour_ambiguous(self):
        """Test bare hour with trigger word - should be ambiguous."""
        result = parse_times("See you at 8")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].hour, 8)
        self.assertIsNone(result[0].minute)
        self.assertIsNone(result[0].am_pm)
        self.assertTrue(result[0].ambiguous)
    
    def test_multiple_times_capped(self):
        """Test that max 3 times are returned."""
        text = "10:00, 11:00, 12:00, 13:00, 14:00"
        result = parse_times(text, max_results=3)
        self.assertEqual(len(result), 3)
    
    def test_no_time_detected(self):
        """Test that empty list is returned when no time found."""
        result = parse_times("Hello world")
        self.assertEqual(len(result), 0)
    
    def test_overlap_detection(self):
        """Test that overlapping matches are handled correctly.
        
        Per TIME_PARSING_RULES.md §1.1: "10:30am" is a 12-hour format with AM/PM.
        TIME_12H_AMPM has priority over TIME_24H to preserve the AM/PM marker.
        """
        result = parse_times("Meeting at 10:30am")
        # Should have only one match - TIME_12H_AMPM wins (more specific)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].hour, 10)
        self.assertEqual(result[0].minute, 30)
        self.assertEqual(result[0].am_pm, "AM")  # AM/PM must be preserved
        self.assertEqual(result[0].raw_text, "10:30am")
    
    def test_overlap_with_bare_hour(self):
        """Test that bare-hour matches are skipped when overlapping."""
        # "at 5pm" matches TIME_12H_AMPM, then TIME_BARE_HOUR should skip due to overlap
        result = parse_times("See you at 5pm")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].hour, 5)
        self.assertEqual(result[0].am_pm, "PM")


if __name__ == '__main__':
    unittest.main()

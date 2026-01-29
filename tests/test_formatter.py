"""
Tests for Telegram adapter formatter.
Specification: ADAPTER_CONTRACTS.md §6
"""
import sys
import unittest
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.contracts import DisplayBlock, DisplayFlags
from adapters.telegram.formatter import (
    format_display_block_with_cities,
    get_cities_for_timezone,
    load_cities_index
)


class TestFormatter(unittest.TestCase):
    """Test DisplayBlock formatting."""
    
    def test_format_with_cities(self):
        """Test formatting with city names."""
        display_block = DisplayBlock(
            entries=(
                {"timezone": "Europe/Amsterdam", "local_time": "10:30", "cities": []},
                {"timezone": "Asia/Yerevan", "local_time": "13:30", "cities": []},
            ),
            ordering="SOURCE_FIRST",
            flags=DisplayFlags(ambiguous=False, partial=False)
        )
        cities_data = [
            {"city": "Amsterdam", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
            {"city": "Yerevan", "country": "AM", "timezone": "Asia/Yerevan", "aliases": []}
        ]
        
        result = format_display_block_with_cities(display_block, cities_data)
        
        self.assertIn("10:30 Europe/Amsterdam (Amsterdam)", result)
        self.assertIn("13:30 Asia/Yerevan (Yerevan)", result)
    
    def test_format_without_cities(self):
        """Test formatting when no cities match timezone."""
        display_block = DisplayBlock(
            entries=(
                {"timezone": "+03:00", "local_time": "13:30", "cities": []},
            ),
            ordering="SOURCE_FIRST",
            flags=DisplayFlags(ambiguous=False, partial=False)
        )
        cities_data = []  # Empty cities
        
        result = format_display_block_with_cities(display_block, cities_data)
        
        # No parentheses when no cities
        self.assertEqual(result, "13:30 +03:00")
    
    def test_format_empty_cities_json(self):
        """Test formatting with empty cities.json.
        
        Per ADAPTER_CONTRACTS.md §5: Empty cities.json is valid state.
        """
        display_block = DisplayBlock(
            entries=(
                {"timezone": "Europe/Amsterdam", "local_time": "10:30", "cities": []},
            ),
            ordering="SOURCE_FIRST",
            flags=DisplayFlags(ambiguous=False, partial=False)
        )
        cities_data = []  # Empty - simulates empty cities.json
        
        result = format_display_block_with_cities(display_block, cities_data)
        
        # No parentheses when cities_data is empty
        self.assertEqual(result, "10:30 Europe/Amsterdam")
    
    def test_get_cities_offset_string(self):
        """Test that offset strings return empty cities list."""
        cities_data = [
            {"city": "Amsterdam", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []}
        ]
        
        result = get_cities_for_timezone("+03:00", cities_data)
        
        self.assertEqual(result, [])
    
    def test_get_cities_max_limit(self):
        """Test that max 3 cities are returned per timezone."""
        cities_data = [
            {"city": "Amsterdam", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
            {"city": "Rotterdam", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
            {"city": "The Hague", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
            {"city": "Utrecht", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
            {"city": "Eindhoven", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []}
        ]
        
        result = get_cities_for_timezone("Europe/Amsterdam", cities_data)
        
        # Max 3 cities, sorted alphabetically
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["Amsterdam", "Eindhoven", "Rotterdam"])
    
    def test_cities_sorted_alphabetically(self):
        """Test that cities are sorted alphabetically (case-insensitive)."""
        cities_data = [
            {"city": "Rotterdam", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
            {"city": "Amsterdam", "country": "NL", "timezone": "Europe/Amsterdam", "aliases": []},
        ]
        
        result = get_cities_for_timezone("Europe/Amsterdam", cities_data)
        
        self.assertEqual(result, ["Amsterdam", "Rotterdam"])


class TestCitiesIndex(unittest.TestCase):
    """Test cities.json index loading."""
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent cities file returns empty index."""
        result = load_cities_index("/nonexistent/path/cities.json")
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()

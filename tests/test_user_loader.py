"""
Tests for user/channel data loader.
Specification: USER_PROFILE_MODEL.md
"""
import sys
import unittest
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from adapters.telegram.user_loader import (
    load_users,
    get_user_profile,
    get_channel_context,
    compute_active_timezones
)


class TestUserLoader(unittest.TestCase):
    """Test user profile loading."""
    
    def test_get_user_profile_known_user(self):
        """Test getting profile for known user."""
        users_data = {
            "telegram:123456789": {"timezone": "Europe/Amsterdam"}
        }
        
        result = get_user_profile("telegram:123456789", users_data)
        
        self.assertEqual(result.timezone, "Europe/Amsterdam")
        self.assertIsNotNone(result.internal_user_id)
    
    def test_get_user_profile_unknown_user(self):
        """Test getting profile for unknown user returns null timezone."""
        users_data = {}
        
        result = get_user_profile("telegram:999999999", users_data)
        
        self.assertIsNone(result.timezone)
        self.assertIsNotNone(result.internal_user_id)
    
    def test_get_user_profile_invalid_timezone(self):
        """Test that invalid timezone is treated as None."""
        users_data = {
            "telegram:123456789": {"timezone": "Invalid/Timezone"}
        }
        
        result = get_user_profile("telegram:123456789", users_data)
        
        self.assertIsNone(result.timezone)
    
    def test_get_user_profile_offset_rejected(self):
        """Test that offset strings in user profile are rejected.
        
        Per USER_PROFILE_MODEL.md §2: Offset strings are NOT allowed in user profiles.
        """
        users_data = {
            "telegram:123456789": {"timezone": "+03:00"}
        }
        
        result = get_user_profile("telegram:123456789", users_data)
        
        # Offset string should be rejected, treated as None
        self.assertIsNone(result.timezone)


class TestChannelContext(unittest.TestCase):
    """Test channel context loading."""
    
    def test_get_channel_context_with_members(self):
        """Test channel context with member timezones."""
        users_data = {
            "telegram:123": {"timezone": "Europe/Amsterdam"},
            "telegram:456": {"timezone": "Asia/Yerevan"},
            "channel:-1001234567890": {
                "default_timezone": "Europe/Amsterdam",
                "members": ["telegram:123", "telegram:456"]
            }
        }
        
        result = get_channel_context("-1001234567890", users_data)
        
        self.assertEqual(result.default_timezone, "Europe/Amsterdam")
        self.assertEqual(set(result.active_timezones), {"Europe/Amsterdam", "Asia/Yerevan"})
    
    def test_get_channel_context_unknown_channel(self):
        """Test unknown channel returns empty context."""
        users_data = {}
        
        result = get_channel_context("-9999999999", users_data)
        
        self.assertIsNone(result.default_timezone)
        self.assertEqual(result.active_timezones, ())
    
    def test_channel_default_timezone_offset_rejected(self):
        """Test that offset strings in channel default_timezone are rejected."""
        users_data = {
            "channel:-1001234567890": {
                "default_timezone": "+03:00",
                "members": []
            }
        }
        
        result = get_channel_context("-1001234567890", users_data)
        
        # Offset string should be rejected
        self.assertIsNone(result.default_timezone)


class TestActiveTimezones(unittest.TestCase):
    """Test active_timezones computation."""
    
    def test_compute_active_timezones_deduplication(self):
        """Test that duplicate timezones are deduplicated.
        
        Per USER_PROFILE_MODEL.md §6.1: Duplicates are automatically deduplicated.
        """
        users_data = {
            "telegram:1": {"timezone": "Europe/Amsterdam"},
            "telegram:2": {"timezone": "Europe/Amsterdam"},
            "telegram:3": {"timezone": "Europe/Amsterdam"},
            "telegram:4": {"timezone": "Asia/Yerevan"}
        }
        channel_config = {
            "members": ["telegram:1", "telegram:2", "telegram:3", "telegram:4"]
        }
        
        result = compute_active_timezones(channel_config, users_data)
        
        # Should be deduplicated and sorted
        self.assertEqual(result, ["Asia/Yerevan", "Europe/Amsterdam"])
    
    def test_compute_active_timezones_sorted(self):
        """Test that active timezones are sorted alphabetically."""
        users_data = {
            "telegram:1": {"timezone": "Europe/London"},
            "telegram:2": {"timezone": "Asia/Tokyo"},
            "telegram:3": {"timezone": "America/New_York"}
        }
        channel_config = {
            "members": ["telegram:1", "telegram:2", "telegram:3"]
        }
        
        result = compute_active_timezones(channel_config, users_data)
        
        self.assertEqual(result, ["America/New_York", "Asia/Tokyo", "Europe/London"])
    
    def test_compute_active_timezones_excludes_null(self):
        """Test that null timezones are excluded."""
        users_data = {
            "telegram:1": {"timezone": "Europe/Amsterdam"},
            "telegram:2": {"timezone": None},
            "telegram:3": {}  # No timezone field
        }
        channel_config = {
            "members": ["telegram:1", "telegram:2", "telegram:3"]
        }
        
        result = compute_active_timezones(channel_config, users_data)
        
        self.assertEqual(result, ["Europe/Amsterdam"])
    
    def test_compute_active_timezones_ignores_unknown_members(self):
        """Test that unknown members are ignored."""
        users_data = {
            "telegram:1": {"timezone": "Europe/Amsterdam"}
        }
        channel_config = {
            "members": ["telegram:1", "telegram:unknown"]
        }
        
        result = compute_active_timezones(channel_config, users_data)
        
        self.assertEqual(result, ["Europe/Amsterdam"])
    
    def test_compute_active_timezones_offset_excluded(self):
        """Test that offset strings in member timezones are excluded."""
        users_data = {
            "telegram:1": {"timezone": "Europe/Amsterdam"},
            "telegram:2": {"timezone": "+03:00"}  # Should be excluded
        }
        channel_config = {
            "members": ["telegram:1", "telegram:2"]
        }
        
        result = compute_active_timezones(channel_config, users_data)
        
        # Only valid IANA timezone should be included
        self.assertEqual(result, ["Europe/Amsterdam"])


class TestLoadUsers(unittest.TestCase):
    """Test users.json loading."""
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file returns empty dict."""
        result = load_users("/nonexistent/path/users.json")
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()

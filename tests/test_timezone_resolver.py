"""
Tests for timezone resolution.
Specification: POLICIES.md §3
"""
import sys
import unittest
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.timezone.resolver import resolve_timezone
from core.contracts import TimezoneSignals, CoreConfig


class TestTimezoneResolver(unittest.TestCase):
    """Test timezone resolution precedence."""
    
    def test_explicit_hint_priority(self):
        """Test that explicit hint has highest priority."""
        signals = TimezoneSignals(
            explicit_timezone="Europe/Amsterdam",
            user_timezone="America/New_York",
            channel_timezone="Asia/Yerevan",
            active_timezones=["Europe/Amsterdam", "America/New_York"]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone=None)
        
        result = resolve_timezone(signals, config)
        self.assertEqual(result.base_timezone, "Europe/Amsterdam")
        self.assertEqual(result.resolution_source, "EXPLICIT_HINT")
        self.assertEqual(result.ambiguity, "NONE")
    
    def test_user_profile_priority(self):
        """Test user profile priority when no explicit hint."""
        signals = TimezoneSignals(
            explicit_timezone=None,
            user_timezone="America/New_York",
            channel_timezone="Asia/Yerevan",
            active_timezones=["Europe/Amsterdam", "America/New_York"]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone=None)
        
        result = resolve_timezone(signals, config)
        self.assertEqual(result.base_timezone, "America/New_York")
        self.assertEqual(result.resolution_source, "USER_PROFILE")
    
    def test_channel_default_priority(self):
        """Test channel default priority."""
        signals = TimezoneSignals(
            explicit_timezone=None,
            user_timezone=None,
            channel_timezone="Asia/Yerevan",
            active_timezones=["Europe/Amsterdam", "America/New_York"]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone=None)
        
        result = resolve_timezone(signals, config)
        self.assertEqual(result.base_timezone, "Asia/Yerevan")
        self.assertEqual(result.resolution_source, "CHANNEL_DEFAULT")
    
    def test_single_active_timezone(self):
        """Test single active timezone resolution."""
        signals = TimezoneSignals(
            explicit_timezone=None,
            user_timezone=None,
            channel_timezone=None,
            active_timezones=["Europe/Amsterdam"]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone=None)
        
        result = resolve_timezone(signals, config)
        self.assertEqual(result.base_timezone, "Europe/Amsterdam")
        self.assertEqual(result.resolution_source, "ACTIVE_TZ_SINGLE")
    
    def test_ambiguity_multiple_active_timezones(self):
        """Test ambiguity when multiple active timezones exist."""
        signals = TimezoneSignals(
            explicit_timezone=None,
            user_timezone=None,
            channel_timezone=None,
            active_timezones=["Europe/Amsterdam", "America/New_York"]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone=None)
        
        result = resolve_timezone(signals, config)
        self.assertIsNone(result.base_timezone)
        self.assertEqual(result.ambiguity, "HIGH")
    
    def test_system_default_fallback(self):
        """Test system default timezone fallback."""
        signals = TimezoneSignals(
            explicit_timezone=None,
            user_timezone=None,
            channel_timezone=None,
            active_timezones=[]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone="UTC")
        
        result = resolve_timezone(signals, config)
        self.assertEqual(result.base_timezone, "UTC")
        self.assertEqual(result.resolution_source, "SYSTEM_DEFAULT")
    
    def test_system_default_null_means_utc(self):
        """Test that config.default_timezone=None means UTC fallback."""
        signals = TimezoneSignals(
            explicit_timezone=None,
            user_timezone=None,
            channel_timezone=None,
            active_timezones=[]
        )
        config = CoreConfig(max_time_mentions=3, max_timezones=5, ordering="SOURCE_FIRST", default_timezone=None)
        
        result = resolve_timezone(signals, config)
        # None should be interpreted as UTC per CONTRACTS.md
        self.assertEqual(result.base_timezone, "UTC")
        self.assertEqual(result.resolution_source, "SYSTEM_DEFAULT")


if __name__ == '__main__':
    unittest.main()

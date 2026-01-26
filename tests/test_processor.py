"""
Tests for core processor - golden test cases.
Specification: END_TO_END_FLOW.md, POLICIES.md
"""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.processor import process
from core.contracts import (
    CoreMessageEvent, UserProfile, ChannelContext, CoreConfig
)


class TestProcessor(unittest.TestCase):
    """Test core processor with golden cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.city_index = {
            "amsterdam": "Europe/Amsterdam",
            "yerevan": "Asia/Yerevan",
            "nyc": "America/New_York",
            "new york": "America/New_York"
        }
        self.config = CoreConfig(
            max_time_mentions=3,
            max_timezones=5,
            ordering="SOURCE_FIRST",
            default_timezone=None
        )
    
    def test_simple_time_with_explicit_timezone(self):
        """Test: 'See you at 10:30 Amsterdam'"""
        event = CoreMessageEvent(
            internal_message_id="test1",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="See you at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=["Europe/Amsterdam", "Asia/Yerevan"]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.entries), 2)  # Amsterdam + Yerevan
        # Check that Amsterdam timezone is first (source)
        self.assertEqual(result.entries[0]["timezone"], "Europe/Amsterdam")
        self.assertEqual(result.entries[0]["local_time"], "10:30")
    
    def test_ambiguous_time_returns_none(self):
        """Test: 'See you at 8' - ambiguous bare hour"""
        event = CoreMessageEvent(
            internal_message_id="test2",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="See you at 8",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=["Europe/Amsterdam"]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        # Should return None due to ambiguity
        self.assertIsNone(result)
    
    def test_no_time_detected_returns_none(self):
        """Test message without time"""
        event = CoreMessageEvent(
            internal_message_id="test3",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Hello world",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=[]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        self.assertIsNone(result)
    
    def test_multiple_active_timezones_no_hint_returns_none(self):
        """Test ambiguity when multiple active timezones and no explicit hint"""
        event = CoreMessageEvent(
            internal_message_id="test4",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=["Europe/Amsterdam", "America/New_York"]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        # Should return None due to ambiguity (multiple active timezones, no hint)
        self.assertIsNone(result)
    
    def test_user_profile_timezone_used(self):
        """Test that user profile timezone is used when no explicit hint"""
        event = CoreMessageEvent(
            internal_message_id="test5",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone="Europe/Amsterdam")
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=["Europe/Amsterdam", "Asia/Yerevan"]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        self.assertIsNotNone(result)
        # Source timezone should be Amsterdam (from user profile)
        self.assertEqual(result.entries[0]["timezone"], "Europe/Amsterdam")
    
    def test_max_time_mentions_limit(self):
        """Test that messages with > max_time_mentions are ignored"""
        # Create message with 4 times (exceeds limit of 3)
        event = CoreMessageEvent(
            internal_message_id="test6",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="10:00, 11:00, 12:00, 13:00",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone="Europe/Amsterdam")
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone="Europe/Amsterdam",
            active_timezones=["Europe/Amsterdam"]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        # Should return None due to exceeding max_time_mentions limit
        self.assertIsNone(result)
    
    def test_partial_flag_when_timezones_omitted(self):
        """Test that partial flag is set when timezones are omitted due to max limit"""
        event = CoreMessageEvent(
            internal_message_id="test7",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        # Create config with max_timezones=2, but provide 5 active timezones
        config = CoreConfig(
            max_time_mentions=3,
            max_timezones=2,  # Limit to 2 timezones
            ordering="SOURCE_FIRST",
            default_timezone=None
        )
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=[
                "Europe/Amsterdam",
                "Asia/Yerevan",
                "America/New_York",
                "Asia/Tokyo",
                "Europe/London"
            ]  # 5 timezones, but max_timezones=2
        )
        
        result = process(event, user_profile, channel_context, self.city_index, config)
        
        self.assertIsNotNone(result)
        # Should have only 2 entries (max_timezones limit)
        self.assertEqual(len(result.entries), 2)
        # partial flag should be True (total candidates > max_timezones AND all slots filled)
        self.assertTrue(result.flags["partial"])
    
    def test_source_first_without_channel_default(self):
        """Test SOURCE_FIRST ordering when channel_default is None"""
        event = CoreMessageEvent(
            internal_message_id="test8",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,  # No channel default
            active_timezones=["Asia/Yerevan", "America/New_York"]
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        self.assertIsNotNone(result)
        # Source timezone (Amsterdam) should be first
        self.assertEqual(result.entries[0]["timezone"], "Europe/Amsterdam")
        # Remaining timezones should be sorted by offset
        # (Yerevan +04:00 should come before New_York -05:00)
        self.assertGreater(len(result.entries), 1)


if __name__ == '__main__':
    unittest.main()

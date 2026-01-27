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
            active_timezones=("Europe/Amsterdam", "Asia/Yerevan")
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.entries), 2)  # Amsterdam + Yerevan
        # Check that Amsterdam timezone is first (source)
        self.assertEqual(result.entries[0]["timezone"], "Europe/Amsterdam")
        self.assertEqual(result.entries[0]["local_time"], "10:30")

    def test_utc_offset_normalized_in_output(self):
        """Test that UTC offset is displayed as IANA ID."""
        event = CoreMessageEvent(
            internal_message_id="test_utc",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 UTC+0",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=()
        )

        result = process(event, user_profile, channel_context, self.city_index, self.config)

        self.assertIsNotNone(result)
        self.assertEqual(result.entries[0]["timezone"], "UTC")
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
            active_timezones=("Europe/Amsterdam",)
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
            active_timezones=()
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
            active_timezones=("Europe/Amsterdam", "America/New_York")
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
            active_timezones=("Europe/Amsterdam", "Asia/Yerevan")
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
            active_timezones=("Europe/Amsterdam",)
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
            active_timezones=(
                "Europe/Amsterdam",
                "Asia/Yerevan",
                "America/New_York",
                "Asia/Tokyo",
                "Europe/London"
            )  # 5 timezones, but max_timezones=2
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
            active_timezones=("Asia/Yerevan", "America/New_York")
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        self.assertIsNotNone(result)
        # Source timezone (Amsterdam) should be first
        self.assertEqual(result.entries[0]["timezone"], "Europe/Amsterdam")
        # Remaining timezones should be sorted by offset
        # (Yerevan +04:00 should come before New_York -05:00)
        self.assertGreater(len(result.entries), 1)
    
    def test_partial_flag_with_conversion_failures(self):
        """Test partial flag edge case: conversion failures should not set partial=True.
        
        Specification: CONTRACTS.md §DisplayBlock - partial flag semantics.
        If some timezones fail to convert, partial=False even if total_candidates > max_timezones.
        """
        event = CoreMessageEvent(
            internal_message_id="test9",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=(
                "Invalid/Timezone1",  # Invalid - will fail conversion
                "Invalid/Timezone2",  # Invalid - will fail conversion
                "Invalid/Timezone3",  # Invalid - will fail conversion
                "Europe/London",      # Valid
                "Asia/Tokyo"         # Valid
            )  # 5 active timezones + 1 source = 6 total, but 3 will fail
        )
        config = CoreConfig(
            max_time_mentions=3,
            max_timezones=5,  # Limit is 5
            ordering="SOURCE_FIRST",
            default_timezone=None
        )
        
        result = process(event, user_profile, channel_context, self.city_index, config)
        
        self.assertIsNotNone(result)
        # Should have source timezone + 2 valid active timezones = 3 entries
        # (3 invalid timezones were excluded due to conversion failures)
        self.assertLess(len(result.entries), config.max_timezones,
                       "Some timezones failed conversion, so not all slots are filled")
        # partial flag should be False because not all slots are filled
        # (even though total_candidates = 6 > max_timezones = 5)
        self.assertFalse(result.flags["partial"],
                        "partial should be False when slots are not filled due to conversion failures")
    
    def test_partial_flag_all_slots_filled(self):
        """Test partial flag: should be True when all slots filled and total_candidates > max_timezones."""
        event = CoreMessageEvent(
            internal_message_id="test10",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone="Europe/London",
            active_timezones=(
                "Asia/Tokyo",
                "America/New_York",
                "Asia/Yerevan",
                "Europe/Paris"
            )  # 1 source + 1 channel default + 4 active = 6 total, max_timezones=5
        )
        config = CoreConfig(
            max_time_mentions=3,
            max_timezones=5,
            ordering="SOURCE_FIRST",
            default_timezone=None
        )
        
        result = process(event, user_profile, channel_context, self.city_index, config)
        
        self.assertIsNotNone(result)
        # Should have exactly 5 entries (max_timezones limit)
        self.assertEqual(len(result.entries), config.max_timezones,
                        "All slots should be filled when valid timezones exceed limit")
        # partial flag should be True (total_candidates > max_timezones AND all slots filled)
        self.assertTrue(result.flags["partial"],
                       "partial should be True when total_candidates > max_timezones AND all slots filled")


    def test_partial_flag_exact_boundary(self):
        """Test partial flag boundary: total_candidates == max_timezones.
        
        When total candidates exactly equals max_timezones, partial should be False
        because no timezones were omitted due to limit.
        """
        event = CoreMessageEvent(
            internal_message_id="test11",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        # Configure exactly 5 unique timezones (source + 4 active = 5 = max_timezones)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=(
                "Asia/Tokyo",
                "America/New_York",
                "Asia/Yerevan",
                "Europe/London"
            )  # 1 source (Amsterdam) + 4 active = 5 total = max_timezones
        )
        config = CoreConfig(
            max_time_mentions=3,
            max_timezones=5,
            ordering="SOURCE_FIRST",
            default_timezone=None
        )
        
        result = process(event, user_profile, channel_context, self.city_index, config)
        
        self.assertIsNotNone(result)
        # Should have exactly 5 entries
        self.assertEqual(len(result.entries), 5,
                        "All 5 timezones should be present")
        # partial flag should be False (total_candidates == max_timezones, no omission)
        self.assertFalse(result.flags["partial"],
                        "partial should be False when total_candidates == max_timezones (no omission)")
    
    def test_text_length_limit(self):
        """Test that very long text is handled gracefully.
        
        Per TIME_PARSING_RULES.md §5: Input is truncated to 4096 chars.
        """
        # Create a very long message with time at the beginning
        long_text = "Meeting at 10:30 Amsterdam " + "x" * 5000
        event = CoreMessageEvent(
            internal_message_id="test12",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text=long_text,
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=("Europe/Amsterdam",)
        )
        
        result = process(event, user_profile, channel_context, self.city_index, self.config)
        
        # Should still process the time at the beginning (within 4096 char limit)
        self.assertIsNotNone(result)
        self.assertEqual(result.entries[0]["timezone"], "Europe/Amsterdam")

    def test_offset_asc_ordering(self):
        """Test OFFSET_ASC ordering strategy.
        
        Entries should be sorted by UTC offset ascending, then alphabetically.
        """
        event = CoreMessageEvent(
            internal_message_id="test_offset_ord",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=("America/New_York", "Asia/Tokyo")  # -05:00 and +09:00
        )
        config = CoreConfig(
            max_time_mentions=3,
            max_timezones=5,
            ordering="OFFSET_ASC",
            default_timezone=None
        )
        
        result = process(event, user_profile, channel_context, self.city_index, config)
        
        self.assertIsNotNone(result)
        # Verify entries are sorted by UTC offset ascending
        # In January: America/New_York (-05:00) < Europe/Amsterdam (+01:00) < Asia/Tokyo (+09:00)
        self.assertEqual(len(result.entries), 3)
        self.assertEqual(result.entries[0]["timezone"], "America/New_York")
        self.assertEqual(result.entries[1]["timezone"], "Europe/Amsterdam")
        self.assertEqual(result.entries[2]["timezone"], "Asia/Tokyo")
    
    def test_alphabetical_ordering(self):
        """Test ALPHABETICAL ordering strategy.
        
        Entries should be sorted alphabetically by timezone ID.
        """
        event = CoreMessageEvent(
            internal_message_id="test_alpha_ord",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 Amsterdam",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        user_profile = UserProfile(internal_user_id="user1", timezone=None)
        channel_context = ChannelContext(
            internal_channel_id="channel1",
            default_timezone=None,
            active_timezones=("Europe/London", "Asia/Tokyo")
        )
        config = CoreConfig(
            max_time_mentions=3,
            max_timezones=5,
            ordering="ALPHABETICAL",
            default_timezone=None
        )
        
        result = process(event, user_profile, channel_context, self.city_index, config)
        
        self.assertIsNotNone(result)
        # Verify entries are sorted alphabetically by timezone ID
        # Asia/Tokyo < Europe/Amsterdam < Europe/London
        self.assertEqual(len(result.entries), 3)
        self.assertEqual(result.entries[0]["timezone"], "Asia/Tokyo")
        self.assertEqual(result.entries[1]["timezone"], "Europe/Amsterdam")
        self.assertEqual(result.entries[2]["timezone"], "Europe/London")


if __name__ == '__main__':
    unittest.main()

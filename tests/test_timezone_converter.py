"""
Tests for timezone converter - partial failure handling.
Specification: CORE_CONTRACT.md §125-147
"""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.timezone.converter import convert_time
from core.contracts import (
    DetectedTime, ResolvedTimeContext, CoreMessageEvent, ConvertedTime
)


class TestTimezoneConverter(unittest.TestCase):
    """Test timezone conversion with edge cases."""
    
    def test_partial_failure_invalid_timezones(self):
        """Test that invalid timezones are skipped, valid ones are returned."""
        detected_time = DetectedTime(
            raw_text="10:30",
            hour=10,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=5,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="Europe/Amsterdam",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        event = CoreMessageEvent(
            internal_message_id="test1",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        # Mix of valid and invalid timezones
        target_timezones = [
            "Europe/Amsterdam",  # Valid
            "Invalid/TZ",        # Invalid
            "America/New_York",  # Valid
            "Bad/Timezone"       # Invalid
        ]
        
        result = convert_time(detected_time, resolved_context, event, target_timezones)
        
        # Should return only valid conversions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].timezone_id, "Europe/Amsterdam")
        self.assertEqual(result[1].timezone_id, "America/New_York")
    
    def test_all_invalid_timezones_returns_empty(self):
        """Test that if all timezones are invalid, empty list is returned."""
        detected_time = DetectedTime(
            raw_text="10:30",
            hour=10,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=5,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="Invalid/TZ",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        event = CoreMessageEvent(
            internal_message_id="test2",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["Invalid/TZ1", "Invalid/TZ2"]
        
        result = convert_time(detected_time, resolved_context, event, target_timezones)
        
        # Should return empty list (all invalid)
        self.assertEqual(len(result), 0)
    
    def test_offset_string_conversion(self):
        """Test conversion with offset strings."""
        detected_time = DetectedTime(
            raw_text="10:30",
            hour=10,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=5,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="+03:00",  # Offset string
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        event = CoreMessageEvent(
            internal_message_id="test3",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 UTC+3",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["+03:00", "-05:00"]  # Offset strings
        
        result = convert_time(detected_time, resolved_context, event, target_timezones)
        
        # Should convert successfully
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].timezone_id, "+03:00")
        self.assertEqual(result[1].timezone_id, "-05:00")
        # Check UTC offset format
        self.assertEqual(result[0].utc_offset, "+03:00")
        self.assertEqual(result[1].utc_offset, "-05:00")

    def test_utc_offset_normalized_to_iana(self):
        """Test that +00:00 is displayed as UTC."""
        detected_time = DetectedTime(
            raw_text="10:30",
            hour=10,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=5,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="+00:00",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        event = CoreMessageEvent(
            internal_message_id="test_utc",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 UTC+0",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["+00:00"]

        result = convert_time(detected_time, resolved_context, event, target_timezones)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].timezone_id, "UTC")
        self.assertEqual(result[0].utc_offset, "+00:00")

    def test_invalid_offset_string_skipped(self):
        """Test that invalid offset strings are skipped."""
        detected_time = DetectedTime(
            raw_text="10:30",
            hour=10,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=5,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="+03:00",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        event = CoreMessageEvent(
            internal_message_id="test4",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 UTC+3",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["+03:00", "+3:00", "Invalid/TZ"]

        result = convert_time(detected_time, resolved_context, event, target_timezones)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].timezone_id, "+03:00")
        self.assertEqual(result[0].utc_offset, "+03:00")

    def test_out_of_range_offset_skipped(self):
        """Test that out-of-range offset strings are skipped."""
        detected_time = DetectedTime(
            raw_text="10:30",
            hour=10,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=5,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="+03:00",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        event = CoreMessageEvent(
            internal_message_id="test5",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 10:30 UTC+3",
            is_edit=False,
            timestamp_utc=datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["+15:00", "+03:00"]  # +15:00 is out of range

        result = convert_time(detected_time, resolved_context, event, target_timezones)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].timezone_id, "+03:00")

    def test_dst_gap_spring_forward(self):
        """Test DST gap (spring forward) handling.
        
        When a time falls in a DST gap (e.g., 2:30 AM when clocks jump from 2:00 to 3:00),
        zoneinfo handles it by moving to the first valid time after the gap.
        
        Specification: POLICIES.md §4.1 - DST handling delegated to zoneinfo.
        """
        # March 29, 2026 - Europe/Amsterdam springs forward at 2:00 AM
        # 2:30 AM doesn't exist, it's in the gap
        detected_time = DetectedTime(
            raw_text="2:30",
            hour=2,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=4,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="Europe/Amsterdam",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        # Use a date when DST transition happens in Europe
        event = CoreMessageEvent(
            internal_message_id="test_dst_gap",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 2:30",
            is_edit=False,
            timestamp_utc=datetime(2026, 3, 29, 1, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["Europe/Amsterdam"]
        
        result = convert_time(detected_time, resolved_context, event, target_timezones)
        
        # Should handle gracefully - zoneinfo will shift to valid time
        # The exact behavior is zoneinfo's default (shift forward)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].timezone_id, "Europe/Amsterdam")
        # During DST gap, time is shifted - we just verify it doesn't crash
        self.assertIsNotNone(result[0].local_time)
    
    def test_dst_fold_fall_back(self):
        """Test DST fold (fall back) handling.
        
        When a time falls in a DST fold (e.g., 2:30 AM when clocks fall back from 3:00 to 2:00),
        zoneinfo uses the first occurrence (pre-transition, fold=0).
        
        Specification: POLICIES.md §4.1 - DST handling delegated to zoneinfo.
        """
        # October 25, 2026 - Europe/Amsterdam falls back at 3:00 AM
        # 2:30 AM occurs twice
        detected_time = DetectedTime(
            raw_text="2:30",
            hour=2,
            minute=30,
            am_pm=None,
            position_start=0,
            position_end=4,
            ambiguous=False
        )
        resolved_context = ResolvedTimeContext(
            base_timezone="Europe/Amsterdam",
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="test"
        )
        # Use a date when DST transition happens in Europe
        event = CoreMessageEvent(
            internal_message_id="test_dst_fold",
            internal_user_id="user1",
            internal_channel_id="channel1",
            text="Meeting at 2:30",
            is_edit=False,
            timestamp_utc=datetime(2026, 10, 25, 1, 0, 0, tzinfo=timezone.utc)
        )
        target_timezones = ["Europe/Amsterdam"]
        
        result = convert_time(detected_time, resolved_context, event, target_timezones)
        
        # Should handle gracefully - zoneinfo uses first occurrence (fold=0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].timezone_id, "Europe/Amsterdam")
        # During DST fold, first occurrence is used - we just verify it doesn't crash
        self.assertIsNotNone(result[0].local_time)


if __name__ == '__main__':
    unittest.main()

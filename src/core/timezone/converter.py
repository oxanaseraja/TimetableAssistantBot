"""
Time conversion to multiple timezones.
Specification: CORE_CONTRACT.md §125-147
"""
import zoneinfo
import re
import logging
from datetime import datetime, time, timedelta, timezone as dt_timezone
from typing import List, Optional
from ..contracts import DetectedTime, ResolvedTimeContext, ConvertedTime, CoreMessageEvent

logger = logging.getLogger(__name__)


def convert_time(
    detected_time: DetectedTime,
    resolved_context: ResolvedTimeContext,
    event: CoreMessageEvent,
    target_timezones: List[str]
) -> List[ConvertedTime]:
    """
    Convert detected time to multiple timezones.
    
    Args:
        detected_time: Detected time from parser
        resolved_context: Resolved timezone context
        event: Message event (for timestamp_utc date reference)
        target_timezones: List of IANA timezone IDs or offset strings (±HH:MM) to convert to
    
    Returns:
        List of ConvertedTime objects
    """
    if resolved_context.base_timezone is None:
        return []
    
    # Build base datetime from detected time
    # Use event.timestamp_utc.date() as reference date for DST
    ref_date = event.timestamp_utc.date()
    
    # Convert hour to 24h format if needed
    hour_24 = detected_time.hour
    if detected_time.am_pm:
        if detected_time.am_pm == "AM":
            if hour_24 == 12:
                hour_24 = 0
        else:  # PM
            if hour_24 != 12:
                hour_24 += 12
    elif detected_time.ambiguous:
        # Ambiguous time - should not reach here (should return None earlier)
        # But handle gracefully
        return []
    
    minute = detected_time.minute if detected_time.minute is not None else 0
    
    # Create naive datetime in base timezone
    base_naive = datetime.combine(ref_date, time(hour_24, minute))
    
    # Make it timezone-aware in base timezone
    # Handle both IANA timezone IDs and offset strings (e.g., "+03:00")
    base_tz = None
    base_timezone_str = resolved_context.base_timezone
    
    # Check if it's an offset string (e.g., "+03:00", "-05:00")
    if re.match(r'^[+-]\d{2}:\d{2}$', base_timezone_str):
        # Parse offset and create fixed offset timezone
        # Validate range: hours [0, 14], minutes [0, 59]
        sign = 1 if base_timezone_str[0] == '+' else -1
        try:
            hours = int(base_timezone_str[1:3])
            minutes = int(base_timezone_str[4:6])
            
            # Validate range per TIMEZONE_EXTRACTION_RULES.md
            if not (0 <= hours <= 14) or not (0 <= minutes <= 59):
                logger.warning(f"Invalid offset range in base_timezone '{base_timezone_str}' (hours must be 0-14, minutes 0-59), returning empty")
                return []
            
            offset_delta = timedelta(hours=hours, minutes=minutes) * sign
            base_tz = dt_timezone(offset_delta)
        except (ValueError, IndexError):
            logger.warning(f"Failed to parse offset string '{base_timezone_str}', returning empty")
            return []
    else:
        # Try as IANA timezone ID
        try:
            base_tz = zoneinfo.ZoneInfo(base_timezone_str)
        except zoneinfo.ZoneInfoNotFoundError:
            # Invalid timezone - return empty
            return []
    
    base_aware = base_naive.replace(tzinfo=base_tz)
    
    # Convert to UTC first
    utc_time = base_aware.astimezone(zoneinfo.ZoneInfo("UTC"))
    
    # Convert to each target timezone
    # Partial Failure Handling: skip invalid timezones, log failures, return successful conversions
    # Specification: CORE_CONTRACT.md §125-147
    results = []
    failed_timezones = []
    
    for tz_id in target_timezones:
        try:
            # Handle offset strings
            if re.match(r'^[+-]\d{2}:\d{2}$', tz_id):
                # Parse offset and create fixed offset timezone
                # Validate range: hours [0, 14], minutes [0, 59]
                sign = 1 if tz_id[0] == '+' else -1
                try:
                    hours = int(tz_id[1:3])
                    minutes = int(tz_id[4:6])
                    
                    # Validate range per TIMEZONE_EXTRACTION_RULES.md
                    if not (0 <= hours <= 14) or not (0 <= minutes <= 59):
                        failed_timezones.append(tz_id)
                        logger.warning(f"Invalid offset range '{tz_id}' (hours must be 0-14, minutes 0-59), skipping")
                        continue
                    
                    offset_delta = timedelta(hours=hours, minutes=minutes) * sign
                    target_tz = dt_timezone(offset_delta)
                except (ValueError, IndexError) as e:
                    failed_timezones.append(tz_id)
                    logger.warning(f"Failed to parse offset string '{tz_id}': {e}, skipping")
                    continue
            else:
                # Try as IANA timezone ID
                try:
                    target_tz = zoneinfo.ZoneInfo(tz_id)
                except zoneinfo.ZoneInfoNotFoundError:
                    failed_timezones.append(tz_id)
                    logger.warning(f"Invalid IANA timezone ID '{tz_id}', skipping")
                    continue
            
            target_time = utc_time.astimezone(target_tz)
            
            # Format UTC offset as ±HH:MM
            # strftime("%z") returns format like "+0100" or "-0500" (5 chars: sign + 4 digits)
            offset = target_time.strftime("%z")
            if offset and len(offset) == 5:
                # Safe to format: "+0100" -> "+01:00"
                offset_formatted = f"{offset[:3]}:{offset[3:]}"
            else:
                # Fallback for edge cases (should not happen with standard zoneinfo)
                offset_formatted = "+00:00"
            
            results.append(ConvertedTime(
                timezone_id=tz_id,
                local_time=target_time,
                utc_offset=offset_formatted
            ))
        except Exception as e:
            # Catch any other unexpected errors
            failed_timezones.append(tz_id)
            logger.warning(f"Unexpected error converting timezone '{tz_id}': {e}, skipping")
            continue
    
    # Log summary if any conversions failed
    if failed_timezones:
        logger.info(f"Failed to convert {len(failed_timezones)} timezone(s): {failed_timezones}, successful conversions: {len(results)}")
    
    return results

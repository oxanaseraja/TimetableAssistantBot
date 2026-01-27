"""
Time conversion to multiple timezones.
Specification: CORE_CONTRACT.md §125-147
"""
import zoneinfo
import re
import logging
from datetime import datetime, time, timedelta, timezone as dt_timezone
from typing import List, Optional, Tuple, Union
from ..contracts import DetectedTime, ResolvedTimeContext, ConvertedTime, CoreMessageEvent

logger = logging.getLogger(__name__)


def parse_offset_to_timezone(offset_str: str) -> Tuple[Optional[dt_timezone], Optional[str]]:
    """
    Parse offset string (±HH:MM) to a fixed-offset timezone object.
    
    Args:
        offset_str: Offset string in format ±HH:MM (e.g., "+03:00", "-05:30")
    
    Returns:
        Tuple of (timezone object, error message)
        - On success: (timezone, None)
        - On failure: (None, error_message)
    
    Validates:
        - Hours: [0, 14]
        - Minutes: [0, 59]
    """
    if not re.match(r'^[+-]\d{2}:\d{2}$', offset_str):
        return None, f"Invalid offset format '{offset_str}'"
    
    sign = 1 if offset_str[0] == '+' else -1
    try:
        hours = int(offset_str[1:3])
        minutes = int(offset_str[4:6])
        
        # Validate range per TIMEZONE_EXTRACTION_RULES.md
        if not (0 <= hours <= 14) or not (0 <= minutes <= 59):
            return None, f"Invalid offset range '{offset_str}' (hours must be 0-14, minutes 0-59)"
        
        offset_delta = timedelta(hours=hours, minutes=minutes) * sign
        return dt_timezone(offset_delta), None
    except (ValueError, IndexError) as e:
        return None, f"Failed to parse offset string '{offset_str}': {e}"


def resolve_timezone_object(tz_id: str) -> Tuple[Optional[Union[dt_timezone, zoneinfo.ZoneInfo]], Optional[str]]:
    """
    Resolve a timezone string to a timezone object.
    
    Supports both IANA timezone IDs and offset strings (±HH:MM).
    
    Args:
        tz_id: IANA timezone ID (e.g., "Europe/Amsterdam") or offset string (e.g., "+03:00")
    
    Returns:
        Tuple of (timezone object, error message)
        - On success: (timezone, None)
        - On failure: (None, error_message)
    """
    # Check if it's an offset string
    if re.match(r'^[+-]\d{2}:\d{2}$', tz_id):
        return parse_offset_to_timezone(tz_id)
    
    # Try as IANA timezone ID
    try:
        return zoneinfo.ZoneInfo(tz_id), None
    except zoneinfo.ZoneInfoNotFoundError:
        return None, f"Invalid IANA timezone ID '{tz_id}'"


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
    base_timezone_str = resolved_context.base_timezone
    base_tz, error = resolve_timezone_object(base_timezone_str)
    if base_tz is None:
        logger.warning(f"Invalid base_timezone: {error}, returning empty")
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
            # Resolve timezone (supports both IANA IDs and offset strings)
            target_tz, error = resolve_timezone_object(tz_id)
            if target_tz is None:
                failed_timezones.append(tz_id)
                logger.warning(f"{error}, skipping")
                continue
            
            target_time = utc_time.astimezone(target_tz)
            
            # Format UTC offset as ±HH:MM
            # strftime("%z") returns format like "+0100" or "-0500" (5 chars: sign + 4 digits)
            offset = target_time.strftime("%z")
            if not offset or len(offset) != 5:
                logger.debug(
                    f"Missing or malformed UTC offset for timezone '{tz_id}' "
                    f"(got '{offset}'), skipping conversion"
                )
                failed_timezones.append(tz_id)
                continue
            # Safe to format: "+0100" -> "+01:00"
            offset_formatted = f"{offset[:3]}:{offset[3:]}"
            
            display_tz_id = "UTC" if offset_formatted == "+00:00" else tz_id
            results.append(ConvertedTime(
                timezone_id=display_tz_id,
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

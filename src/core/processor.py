"""
Main core processor - orchestrates time parsing, timezone resolution, and conversion.
Specification: CORE_CONTRACT.md
"""
import logging
from typing import Mapping, Optional
from .contracts import (
    CoreMessageEvent, UserProfile, ChannelContext, CoreConfig,
    DetectedTime, TimezoneSignals, ResolvedTimeContext, ConvertedTime, DisplayBlock
)
from .parser.time_parser import parse_times
from .timezone.extractor import extract_timezone_hint
from .timezone.resolver import resolve_timezone
from .timezone.converter import convert_time

logger = logging.getLogger(__name__)


def process(
    event: CoreMessageEvent,
    user_profile: UserProfile,
    channel_context: ChannelContext,
    city_index: Mapping[str, str],
    config: CoreConfig
) -> Optional[DisplayBlock]:
    """
    Main core processing function.
    
    Args:
        event: The message to process
        user_profile: Timezone info for message author (may have null timezone)
        channel_context: Channel default and active timezones
        city_index: Pre-built city→timezone lookup table (from cities.json)
        config: Processing configuration (limits, ordering, defaults)
    
    Returns:
        DisplayBlock — formatted output for adapter to render
        None — no output (no time detected, ambiguity, suppression)
    
    Rules:
    - Synchronous call — no async, no callbacks
    - Pure function — no side effects, no I/O, no storage access
    - Deterministic — same inputs always produce same output
    - Never raises exceptions — all errors result in None
    """
    try:
        # Step 1: Parse times from message text
        # Parse with limit+1 to detect if message exceeds limit without parsing all matches
        all_times = parse_times(event.text, max_results=config.max_time_mentions + 1)
        
        # Use only first max_time_mentions times
        detected_times = all_times[:config.max_time_mentions]
        # Track time mention truncation for diagnostics only
        time_mentions_truncated = len(all_times) > config.max_time_mentions
        
        # Stop if no time detected
        if not detected_times:
            logger.debug("Message discarded: no time detected")
            return None
        
        # MVP simplification: Process only the first detected time (SPEC_FREEZE §3.1)
        detected_time = detected_times[0]
        logger.debug(
            f"Detected time: {detected_time.raw_text} "
            f"(hour={detected_time.hour}, minute={detected_time.minute}, am_pm={detected_time.am_pm}, "
            f"mentions_truncated={time_mentions_truncated})"
        )
        
        # Stop if time is ambiguous (bare hour without am/pm)
        if detected_time.ambiguous:
            logger.debug(f"Message discarded: ambiguous time '{detected_time.raw_text}' (bare hour without AM/PM)")
            return None
        
        # Step 2: Extract timezone signals
        explicit_tz = extract_timezone_hint(
            event.text,
            detected_time.position_start,
            city_index,
            window=30
        )
        logger.debug(f"Extracted timezone hint: {explicit_tz}")
        
        signals = TimezoneSignals(
            explicit_timezone=explicit_tz,
            user_timezone=user_profile.timezone,
            channel_timezone=channel_context.default_timezone,
            active_timezones=channel_context.active_timezones
        )
        logger.debug(f"Timezone signals: explicit={explicit_tz}, user={user_profile.timezone}, channel={channel_context.default_timezone}, active={len(channel_context.active_timezones)}")
        
        # Step 3: Resolve timezone
        resolved_context = resolve_timezone(signals, config)
        logger.debug(f"Resolved timezone: {resolved_context.base_timezone} (source={resolved_context.resolution_source}, ambiguity={resolved_context.ambiguity})")
        
        # Stop if ambiguous
        if resolved_context.ambiguity == "HIGH":
            logger.debug(f"Message discarded: timezone ambiguity HIGH - {resolved_context.reason}")
            return None
        
        if resolved_context.base_timezone is None:
            logger.debug("Message discarded: no base_timezone resolved")
            return None
        
        # Step 4: Determine target timezones for conversion
        # Include source timezone, channel default, and active timezones
        # Build prioritized list: source first, then channel default, then active_timezones
        # This preserves order for SOURCE_FIRST ordering strategy
        target_timezones_list = []
        
        # Always include source timezone first
        if resolved_context.base_timezone:
            target_timezones_list.append(resolved_context.base_timezone)
        
        # Include channel default if different from source (second priority)
        # Edge case: If source is offset string (e.g., "+02:00") and channel default is IANA ID
        # with same offset (e.g., "Europe/Amsterdam" in winter = UTC+2), we still include both
        # because they are semantically different (offset string vs named timezone with DST).
        # However, if they are string-equal, skip to avoid duplicate.
        if channel_context.default_timezone and channel_context.default_timezone != resolved_context.base_timezone:
            if channel_context.default_timezone not in target_timezones_list:
                target_timezones_list.append(channel_context.default_timezone)
        
        # Include active timezones (up to max_timezones limit)
        # Edge case: Empty active_timezones is valid state per POLICIES.md §5
        # System gracefully handles channels with no known member timezones
        for tz in channel_context.active_timezones:
            if len(target_timezones_list) >= config.max_timezones:
                break
            if tz not in target_timezones_list:  # Avoid duplicates (edge case: duplicate timezones)
                target_timezones_list.append(tz)
        
        # Apply limit (already enforced above, but ensure)
        target_timezones_list = target_timezones_list[:config.max_timezones]
        
        # Step 5: Convert time to target timezones
        logger.debug(f"Converting time to {len(target_timezones_list)} timezone(s): {target_timezones_list}")
        converted_times = convert_time(
            detected_time,
            resolved_context,
            event,
            target_timezones_list
        )
        
        if not converted_times:
            logger.debug("Message discarded: no successful time conversions (all timezones failed or empty target list)")
            return None
        
        logger.debug(f"Successfully converted to {len(converted_times)} timezone(s)")
        logger.debug(f"Converted times: {[(ct.timezone_id, ct.local_time.strftime('%H:%M'), ct.utc_offset) for ct in converted_times]}")
        
        # Step 6: Build DisplayBlock
        # Sort entries according to ordering strategy
        entries = []
        for conv_time in converted_times:
            # Format time as HH:MM (24-hour, zero-padded)
            time_str = conv_time.local_time.strftime("%H:%M")
            
            entries.append({
                "timezone": conv_time.timezone_id,
                "local_time": time_str,
                "cities": []  # Adapter will populate cities
            })
        
        logger.debug(f"Entries before sorting: {[(e['timezone'], e['local_time']) for e in entries]}")
        
        # Apply ordering
        if config.ordering == "SOURCE_FIRST":
            # SOURCE_FIRST ordering strategy (CONTRACTS.md §111-114):
            # 1. Source timezone first (where original time was expressed)
            # 2. Channel default timezone second (if different from source)
            # 3. Remaining active timezones ordered by UTC offset ascending, then alphabetically
            #
            # Edge cases:
            # - If channel_default_timezone is None → skip priority 1, go directly to offset sorting
            # - If channel_default_timezone == source_timezone → don't duplicate, skip priority 1
            source_tz = resolved_context.base_timezone
            channel_tz = channel_context.default_timezone
            
            def sort_key(entry):
                tz = entry["timezone"]
                # Priority 0: Source timezone (always first)
                if tz == source_tz:
                    return (0, 0, tz)
                # Priority 1: Channel default timezone (if exists and different from source)
                elif channel_tz and tz == channel_tz:
                    return (1, 0, tz)
                # Priority 2: Remaining timezones sorted by UTC offset, then alphabetically
                else:
                    # Get offset for sorting
                    conv = next((c for c in converted_times if c.timezone_id == tz), None)
                    if conv:
                        offset_str = conv.utc_offset
                        # Parse ±HH:MM to integer minutes for sorting
                        # Protected by try/except per ARCHITECTURAL_INVARIANTS.md #8
                        try:
                            sign = 1 if offset_str[0] == '+' else -1
                            hours = int(offset_str[1:3])
                            minutes = int(offset_str[4:6])
                            offset_minutes = sign * (hours * 60 + minutes)
                        except (ValueError, IndexError):
                            offset_minutes = 0  # Fallback for malformed offset
                        return (2, offset_minutes, tz)
                    return (2, 0, tz)
            
            entries.sort(key=sort_key)
        elif config.ordering == "OFFSET_ASC":
            # Sort by UTC offset ascending, then alphabetically by ID
            def sort_key(entry):
                tz = entry["timezone"]
                conv = next((c for c in converted_times if c.timezone_id == tz), None)
                if conv:
                    offset_str = conv.utc_offset
                    # Protected by try/except per ARCHITECTURAL_INVARIANTS.md #8
                    try:
                        sign = 1 if offset_str[0] == '+' else -1
                        hours = int(offset_str[1:3])
                        minutes = int(offset_str[4:6])
                        offset_minutes = sign * (hours * 60 + minutes)
                    except (ValueError, IndexError):
                        offset_minutes = 0  # Fallback for malformed offset
                    return (offset_minutes, tz)
                return (0, tz)
            
            entries.sort(key=sort_key)
        elif config.ordering == "ALPHABETICAL":
            # Sort alphabetically by timezone ID
            entries.sort(key=lambda e: e["timezone"])
        
        # Check if partial (some timezones omitted due to max limit)
        # Specification: CONTRACTS.md §DisplayBlock - partial flag semantics
        # partial = true if total candidates exceed max_timezones, regardless of conversion failures
        total_candidates = set()
        if resolved_context.base_timezone:
            total_candidates.add(resolved_context.base_timezone)
        if channel_context.default_timezone:
            total_candidates.add(channel_context.default_timezone)
        total_candidates.update(channel_context.active_timezones)
        
        partial = len(total_candidates) > config.max_timezones
        
        return DisplayBlock(
            entries=entries,
            ordering=config.ordering,
            flags={
                "ambiguous": False,  # If truly ambiguous, we return None earlier
                "partial": partial
            }
        )
    
    except Exception:
        # Invariant #8: Core never raises uncaught exceptions
        # All errors result in None
        # Log exception for diagnostics (allowed per CORE_CONTRACT.md Rule 2)
        logger.exception("Unexpected error in processor, returning None")
        return None

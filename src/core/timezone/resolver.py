"""
Timezone resolution logic.
Specification: POLICIES.md §3
"""
from typing import Optional, Literal
from ..contracts import TimezoneSignals, ResolvedTimeContext, CoreConfig


def resolve_timezone(
    signals: TimezoneSignals,
    config: CoreConfig
) -> ResolvedTimeContext:
    """
    Resolve timezone from signals using priority order.
    
    Priority order:
    1. EXPLICIT_HINT — Explicit offset in text (UTC+2, +0300)
    2. EXPLICIT_HINT — Explicit IANA timezone name
    3. EXPLICIT_HINT — City extracted from text
    4. USER_PROFILE — User profile timezone
    5. CHANNEL_DEFAULT — Channel default timezone
    6. ACTIVE_TZ_SINGLE — If exactly one active timezone → use it
    7. SYSTEM_DEFAULT — Fallback to UTC (if configured) or ambiguity
    
    Returns:
        ResolvedTimeContext with base_timezone or None if ambiguous
    """
    # Priority 1-3: Explicit hint (offset/IANA/city) is resolved in extractor
    # Note: Resolver does NOT validate timezone format (IANA vs offset)
    # Format validation is responsibility of converter (CORE_CONTRACT.md)
    if signals.explicit_timezone:
        return ResolvedTimeContext(
            base_timezone=signals.explicit_timezone,
            ambiguity="NONE",
            resolution_source="EXPLICIT_HINT",
            reason="explicit hint in text"
        )
    
    # Priority 4: User profile (after explicit hint resolution in extractor)
    if signals.user_timezone:
        return ResolvedTimeContext(
            base_timezone=signals.user_timezone,
            ambiguity="NONE",
            resolution_source="USER_PROFILE",
            reason="from user profile"
        )
    
    # Priority 5: Channel default (after explicit hint resolution in extractor)
    if signals.channel_timezone:
        return ResolvedTimeContext(
            base_timezone=signals.channel_timezone,
            ambiguity="NONE",
            resolution_source="CHANNEL_DEFAULT",
            reason="from channel default"
        )
    
    # Priority 6: Single active timezone (after explicit hint resolution in extractor)
    # Edge case: Empty active_timezones (len == 0) falls through to SYSTEM_DEFAULT
    if len(signals.active_timezones) == 1:
        return ResolvedTimeContext(
            base_timezone=signals.active_timezones[0],
            ambiguity="NONE",
            resolution_source="ACTIVE_TZ_SINGLE",
            reason="only one active timezone"
        )
    
    # Priority 7: System default or ambiguity (after explicit hint resolution in extractor)
    # Specification: POLICIES.md §68-72, CORE_CONTRACT.md §89-97
    # config.default_timezone = null means system UTC (per CONTRACTS.md)
    # Resolver MUST interpret null as "UTC" when producing ResolvedTimeContext.base_timezone
    # This is the single source of truth for fallback timezone resolution
    
    # Check for ambiguity first (multiple active timezones)
    # This is HIGH ambiguity per POLICIES.md §4 - no reply sent
    if len(signals.active_timezones) > 1:
        return ResolvedTimeContext(
            base_timezone=None,
            ambiguity="HIGH",
            resolution_source=None,
            reason="multiple active timezones, no explicit hint"
        )
    
    # System default: interpret None as "UTC" (explicit interpretation required by specification)
    # This ensures base_timezone is always a string (IANA ID or offset) when ambiguity = "NONE"
    # base_timezone may be None ONLY when ambiguity = "HIGH"
    system_default_tz = config.default_timezone if config.default_timezone else "UTC"
    return ResolvedTimeContext(
        base_timezone=system_default_tz,
        ambiguity="NONE",
        resolution_source="SYSTEM_DEFAULT",
        reason="no timezone information, using system default"
    )

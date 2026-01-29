"""
Core DTOs (Data Transfer Objects) as defined in CONTRACTS.md
All DTOs are immutable dataclasses.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Literal, Mapping, TypedDict, Tuple


@dataclass(frozen=True)
class CoreMessageEvent:
    """Message event passed to core from adapter."""
    internal_message_id: str  # SHA256 hash, hex encoded
    internal_user_id: str  # SHA256 hash, hex encoded
    internal_channel_id: str  # SHA256 hash, hex encoded
    text: str  # original message text
    is_edit: bool  # true if this is an edit event
    timestamp_utc: datetime  # timezone-aware, UTC (used for DST)


@dataclass(frozen=True)
class DetectedTime:
    """Detected time mention in message."""
    raw_text: str
    hour: int
    minute: Optional[int]
    am_pm: Optional[Literal["AM", "PM"]]
    position_start: int
    position_end: int
    ambiguous: bool


@dataclass(frozen=True)
class TimezoneSignals:
    """Timezone hints extracted from message and context.
    
    Note: active_timezones is a Tuple (immutable) to ensure full immutability
    of the frozen dataclass. See ARCHITECTURAL_INVARIANTS.md #6.
    """
    explicit_timezone: Optional[str]  # IANA id or offset
    user_timezone: Optional[str]
    channel_timezone: Optional[str]
    active_timezones: Tuple[str, ...]  # Immutable tuple for full immutability


@dataclass(frozen=True)
class ResolvedTimeContext:
    """Resolved timezone context for time conversion."""
    base_timezone: Optional[str]
    ambiguity: Literal["NONE", "HIGH"]
    resolution_source: Optional[Literal[
        "EXPLICIT_HINT", "USER_PROFILE", "CHANNEL_DEFAULT",
        "ACTIVE_TZ_SINGLE", "SYSTEM_DEFAULT"
    ]]
    reason: Optional[str]


@dataclass(frozen=True)
class ConvertedTime:
    """Time converted to a specific timezone."""
    timezone_id: str
    local_time: datetime  # timezone-aware datetime
    utc_offset: str  # ±HH:MM format


class Entry(TypedDict):
    """Single timezone entry in DisplayBlock."""
    timezone: str
    local_time: str
    cities: List[str]  # Populated by adapter, not core


@dataclass(frozen=True)
class DisplayFlags:
    """Display flags for DisplayBlock.
    
    Changed from TypedDict to frozen dataclass for full immutability.
    See ARCHITECTURAL_INVARIANTS.md #6.
    """
    ambiguous: bool
    partial: bool


@dataclass(frozen=True)
class DisplayBlock:
    """Formatted output for adapter to render.
    
    Note: entries is a Tuple (immutable) to ensure full immutability
    of the frozen dataclass. See ARCHITECTURAL_INVARIANTS.md #6.
    """
    entries: Tuple[Entry, ...]  # Immutable tuple for full immutability
    ordering: Literal["SOURCE_FIRST", "OFFSET_ASC", "ALPHABETICAL"]
    flags: DisplayFlags


@dataclass(frozen=True)
class CoreConfig:
    """Configuration for core processing logic."""
    max_time_mentions: int  # max times to process per message (default: 3)
    max_timezones: int  # max timezones in DisplayBlock (default: 5)
    ordering: Literal["SOURCE_FIRST", "OFFSET_ASC", "ALPHABETICAL"]  # output ordering
    default_timezone: Optional[str]  # system fallback timezone (default: null = UTC)


@dataclass(frozen=True)
class UserProfile:
    """User profile with timezone information."""
    internal_user_id: str
    timezone: Optional[str]  # IANA timezone ID or null


@dataclass(frozen=True)
class ChannelContext:
    """Channel context with default and active timezones.
    
    Note: active_timezones is a Tuple (immutable) to ensure full immutability
    of the frozen dataclass. See ARCHITECTURAL_INVARIANTS.md #6.
    """
    internal_channel_id: str
    default_timezone: Optional[str]
    active_timezones: Tuple[str, ...]  # Immutable tuple for full immutability

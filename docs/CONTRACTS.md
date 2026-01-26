# CONTRACTS.md — Core DTO Pack (MVP)

Contracts are deterministic and platform-agnostic.
Core never receives platform identifiers.
MVP platform: Telegram.

---

## CoreMessageEvent

```
CoreMessageEvent {
    internal_message_id: string,   // SHA256 hash, hex encoded
    internal_user_id: string,      // SHA256 hash, hex encoded
    internal_channel_id: string,   // SHA256 hash, hex encoded
    text: string,                  // original message text
    is_edit: boolean,              // true if this is an edit event
    timestamp_utc: datetime        // timezone-aware, UTC (used for DST)
}
```

**Note:** `timestamp_utc` must be a timezone-aware datetime object in UTC.
Used as reference date for DST calculations.

---

## DetectedTime

```
DetectedTime {
    raw_text: string,
    hour: int,
    minute?: int,
    am_pm?: "AM" | "PM",
    position_start: int,
    position_end: int,
    ambiguous: boolean
}
```

---

## TimezoneSignals

```
TimezoneSignals {
    explicit_timezone?: string,   // IANA id or offset
    user_timezone?: string,
    channel_timezone?: string,
    active_timezones: List<string>
}
```

---

## ResolvedTimeContext

```
ResolvedTimeContext {
    base_timezone?: string,
    ambiguity: "NONE" | "HIGH",
    resolution_source?: ResolutionSource,
    reason?: string
}

ResolutionSource = "EXPLICIT_HINT" | "USER_PROFILE" | "CHANNEL_DEFAULT" | "ACTIVE_TZ_SINGLE" | "SYSTEM_DEFAULT"
```

**ResolutionSource values:**
- `EXPLICIT_HINT` — timezone found in message text (offset, IANA ID, or city)
- `USER_PROFILE` — from author's UserProfile.timezone
- `CHANNEL_DEFAULT` — from ChannelContext.default_timezone
- `ACTIVE_TZ_SINGLE` — only one timezone in active_timezones
- `SYSTEM_DEFAULT` — fallback to UTC when no other source available

---

## ConvertedTime

```
ConvertedTime {
    timezone_id: string,
    local_time: datetime,
    utc_offset: string
}
```

---

## DisplayBlock

```
DisplayBlock {
    entries: List<{
        timezone: string,       // IANA timezone ID
        local_time: string,     // HH:MM format (24-hour, zero-padded)
        cities: List<string>    // populated by adapter from cities.json
    }>,
    ordering: Ordering,
    flags: DisplayFlags
}

Ordering = "SOURCE_FIRST" | "OFFSET_ASC" | "ALPHABETICAL"
// SOURCE_FIRST: source timezone first, then channel default, then by offset
// OFFSET_ASC: sorted by UTC offset ascending, then alphabetically by ID
// ALPHABETICAL: sorted alphabetically by timezone ID

DisplayFlags {
    ambiguous: boolean,   // true if any input time was ambiguous
    partial: boolean      // true if some timezones were omitted due to max limit (5)
}
```

**Notes:**
- `partial = true` only when `len(active_timezones) > max_display_limit`
- `ambiguous` is informational; if truly ambiguous, core returns None instead
- Adapter uses `ordering` to verify output order matches expectation

---

## CoreConfig

```
CoreConfig {
    max_time_mentions: int,     // max times to process per message (default: 3)
    max_timezones: int,         // max timezones in DisplayBlock (default: 5)
    ordering: Ordering,         // output ordering strategy
    default_timezone: string?   // system fallback timezone (default: null = UTC)
}
```

**Purpose:** Configuration for core processing logic. Passed as argument to maintain purity (no global config access).

**Defaults:**
- `max_time_mentions = 3` (from POLICIES.md §2)
- `max_timezones = 5` (from POLICIES.md §2)
- `ordering = "SOURCE_FIRST"` (from POLICIES.md §6)
- `default_timezone = null` (null means UTC)

**Mapping from configuration.yaml:**
- `core.max_time_mentions` → `CoreConfig.max_time_mentions`
- `output.max_timezones` → `CoreConfig.max_timezones`
- `output.ordering` → `CoreConfig.ordering`
- (no config key) → `CoreConfig.default_timezone` (hardcoded or absent)

---

## CityIndex

**Type:** `Mapping[str, str]` — lowercase name/alias → IANA timezone ID

**Purpose:** Pre-built lookup table for city-to-timezone resolution.

**Construction:** See TIMEZONE_EXTRACTION_RULES.md §2.1

**Why passed as argument:**
- Core cannot load files (Invariant #2)
- Adapter owns `cities.json` and builds index at startup
- Passing as argument maintains core purity (Invariant #7)

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
```

**Note:**
- `base_timezone` is always a string (IANA ID or offset string) when present, never null
- When `config.default_timezone = null`, resolver interprets it as `"UTC"` and returns `base_timezone = "UTC"`
- `base_timezone` may be `None` only when ambiguity is `"HIGH"` (multiple conflicting sources)

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
    entries: List<Entry>,
    ordering: Ordering,
    flags: DisplayFlags
}

Entry {
    timezone: string,       // IANA timezone ID or offset string (±HH:MM)
    local_time: string,     // "HH:MM", 24-hour format, zero-padded (e.g., "10:30", "09:05")
    cities: List<string>    // List of city names (may be empty, adapter populates)
}
```

**Entry structure specification:**

Entry is a dictionary/object with exactly these three fields:

- `timezone`: 
  - Type: `string`
  - Always a string (IANA ID or offset string)
  - IANA timezone ID (e.g., `"Europe/Amsterdam"`) OR
  - Offset string in normalized format (e.g., `"+03:00"`, `"-05:00"`)
  - Offset strings may appear when extracted from message text (see `TIMEZONE_EXTRACTION_RULES.md`)

- `local_time`: 
  - Type: `string`
  - Always formatted as `"HH:MM"` (24-hour format, zero-padded, no seconds, no AM/PM)
  - Examples: `"10:30"`, `"09:05"`, `"23:59"`
  - Format: exactly 5 characters (`HH:MM`)

- `cities`: 
  - Type: `List[string]`
  - Always a list (may be empty `[]`)
  - List of city names matching this timezone
  - Adapter populates from `cities.json` during formatting
  - Cities are sorted alphabetically
  - Empty list `[]` if no cities match or if timezone is an offset string

Ordering = "SOURCE_FIRST" | "OFFSET_ASC" | "ALPHABETICAL"
// SOURCE_FIRST: source timezone first, then channel default, then by offset
//   - Source timezone (where original time was expressed) is always first
//   - Channel default timezone is second (if exists and different from source)
//   - Remaining active timezones are sorted by UTC offset ascending, then alphabetically
//   Edge cases:
//   - If channel_default_timezone is None → skip channel default priority, 
//     remaining timezones sorted by offset
//   - If channel_default_timezone == source_timezone → don't duplicate,
//     skip channel default priority, remaining timezones sorted by offset
// OFFSET_ASC: sorted by UTC offset ascending, then alphabetically by ID
// ALPHABETICAL: sorted alphabetically by timezone ID

DisplayFlags {
    ambiguous: boolean,   // true if any input time was ambiguous
    partial: boolean      // true if some timezones were omitted due to max limit (5)
}
```

**Entry format specification:**

- `timezone`: 
  - IANA timezone ID (e.g., `"Europe/Amsterdam"`) OR
  - Offset string in normalized format (e.g., `"+03:00"`, `"-05:00"`)
  - Offset strings may appear when extracted from message text (see `TIMEZONE_EXTRACTION_RULES.md`)

- `local_time`: 
  - Always formatted as `"HH:MM"` (24-hour format, zero-padded)
  - Examples: `"10:30"`, `"09:05"`, `"23:59"`

- `cities`: 
  - List of city names matching this timezone
  - May be empty list `[]`
  - Adapter populates from `cities.json` during formatting
  - Cities are sorted alphabetically

**Ordering rules:**
- `entries` must be ordered according to `ordering` strategy
- Order is determined by core processor
- Adapter must preserve order when formatting

**Notes:**
- `ambiguous` is informational; if truly ambiguous, core returns None instead
- Adapter uses `ordering` to verify output order matches expectation

**partial flag semantics:**

`partial = true` iff:
- total number of candidate timezones
  (base + channel default + active_timezones)
  > max_timezones
AND
- displayed entries == max_timezones

Meaning:
Some valid conversions were omitted due to display limit.

**Critical edge case: Partial conversion failures**

If some timezones fail to convert (e.g., invalid IANA ID, conversion errors):
- Failed conversions are excluded from `displayed entries`
- `partial` flag is set to `true` ONLY if:
  - `total_candidates > max_timezones` AND
  - `len(displayed_entries) == max_timezones` (all available slots are filled with successful conversions)
- If `len(displayed_entries) < max_timezones` due to conversion failures:
  - `partial = false` (even if `total_candidates > max_timezones`)
  - This indicates that not all slots were filled, so no timezones were omitted due to limit

**Examples:**
- `total_candidates = 6`, `max_timezones = 5`, `displayed_entries = 5` → `partial = true` (1 omitted due to limit)
- `total_candidates = 6`, `max_timezones = 5`, `displayed_entries = 3` (3 failed) → `partial = false` (slots not filled, failures not due to limit)
- `total_candidates = 3`, `max_timezones = 5`, `displayed_entries = 3` → `partial = false` (no limit reached)

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

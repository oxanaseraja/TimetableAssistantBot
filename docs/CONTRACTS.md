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

## Timezone Identity Model

**Critical rule:** The system distinguishes timezones by their **string identifier**, not by their effective UTC offset.

**Timezone identity types:**

1. **IANA timezone identifiers** (e.g., `"Europe/Amsterdam"`, `"America/New_York"`)
   - Named timezones with DST support
   - Stable identifiers across time periods
   - May have associated cities in `cities.json`

2. **Fixed UTC offset strings** (e.g., `"+02:00"`, `"-05:00"`)
   - Anonymous timezones without DST
   - Normalized format: `±HH:MM` (e.g., `"+03:00"`, `"-05:30"`)
   - No associated cities (offset strings don't map to cities)

**Identity rule:**

Timezones are treated as **distinct identities** if their string identifiers differ, even if their effective UTC offset at a given timestamp is equal.

**Examples:**
- `"+02:00"` and `"Europe/Amsterdam"` → **two distinct timezones**
  - Even if `Europe/Amsterdam` has UTC+2 offset in January (winter time)
  - They are compared by exact string match: `"+02:00" != "Europe/Amsterdam"`
- `"Europe/Amsterdam"` and `"Europe/Berlin"` → **two distinct timezones**
  - Even if they have the same offset (both UTC+1/UTC+2 with DST)
  - They are compared by exact string match: `"Europe/Amsterdam" != "Europe/Berlin"`

**Rationale:**
- **Deterministic:** String comparison is unambiguous and predictable
- **No hidden heuristics:** No semantic equivalence checks by offset
- **DST-aware:** IANA IDs carry DST information, offset strings don't
- **Simple specification:** Easy to understand and implement
- **Prevents DST traps:** Offset strings and IANA IDs behave differently over time

**Implications:**
- Deduplication uses exact string identity only
- Multiple timezones with same offset may appear in output
- Converter preserves original timezone identifier (no normalization to IANA ID)

**See also:**
- `CORE_CONTRACT.md` §Target Timezone List Construction — how deduplication is applied
- `CONTRACTS.md` §DisplayBlock — display semantics for multiple timezones with same offset

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

**Examples:**

Example 1: Explicit hint in text
```
Input: "Meeting at 10:30 UTC+3"
ResolvedTimeContext:
  base_timezone: "+03:00"
  ambiguity: "NONE"
  resolution_source: "EXPLICIT_HINT"
  reason: "explicit hint in text"
```

Example 2: User profile timezone
```
Input: "Call at 14:00"
UserProfile.timezone: "Europe/Amsterdam"
ResolvedTimeContext:
  base_timezone: "Europe/Amsterdam"
  ambiguity: "NONE"
  resolution_source: "USER_PROFILE"
  reason: "from user profile"
```

Example 3: System default (null → UTC)
```
Input: "Meeting at 10:00"
config.default_timezone: null
No explicit hint, no user/channel timezone
ResolvedTimeContext:
  base_timezone: "UTC"
  ambiguity: "NONE"
  resolution_source: "SYSTEM_DEFAULT"
  reason: "no timezone information, using system default"
```

Example 4: High ambiguity
```
Input: "Call at 10:00"
active_timezones: ["Europe/Amsterdam", "America/New_York", "Asia/Tokyo"]
No explicit hint, no user/channel default
ResolvedTimeContext:
  base_timezone: None
  ambiguity: "HIGH"
  resolution_source: None
  reason: "multiple active timezones, no explicit hint"
```

ResolutionSource = "EXPLICIT_HINT" | "USER_PROFILE" | "CHANNEL_DEFAULT" | "ACTIVE_TZ_SINGLE" | "SYSTEM_DEFAULT"
```

**ResolutionSource values:**
- `EXPLICIT_HINT` — timezone found in message text (offset, IANA ID, or city)
- `USER_PROFILE` — from author's UserProfile.timezone
- `CHANNEL_DEFAULT` — from ChannelContext.default_timezone
- `ACTIVE_TZ_SINGLE` — only one timezone in active_timezones
- `SYSTEM_DEFAULT` — fallback to UTC when no other source available

**Explicit hint vs user profile behavior:**

When an explicit hint is present in the message text:
- Explicit hint becomes `base_timezone` (source timezone for conversion)
- User profile timezone is **NOT** used as `base_timezone`
- User profile timezone **MAY** still appear in output as an active timezone

Example:
```
User profile: Europe/Amsterdam
Message: "Meeting at 10:30 UTC+3"
Explicit hint: +03:00

Result:
- base_timezone = "+03:00" (from explicit hint)
- Europe/Amsterdam may appear in output if it's in active_timezones
- Output shows time in +03:00 first, then other active timezones
```

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
  - **UTC format rule:** UTC must be displayed as IANA ID `"UTC"`, not as offset `"+00:00"`

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

**Note on cities field ownership:**

- Core processor always returns `cities: []` (empty list)
- Adapter populates cities during formatting using `get_cities_for_timezone()`
- This separation ensures core remains pure (no filesystem / data access)
- Core does not know about cities.json (see `ARCHITECTURAL_INVARIANTS.md` #2)

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
//   Deduplication: Comparison uses exact string identity (see Timezone Identity Model)
//     - Deduplication MAY be applied during target list construction
//     - Final list must contain unique timezone identifiers and respect max_timezones
//     - "+02:00" != "Europe/Amsterdam" (different strings, both included)
//     - "Europe/Amsterdam" == "Europe/Amsterdam" (same string, duplicate removed)
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

**Display semantics:**

**See also:** `CONTRACTS.md` §Timezone Identity Model and `CORE_CONTRACT.md` §Target Timezone List Construction.

**Critical rule:** If multiple timezones produce identical local times, they may still be displayed separately if their identifiers differ.

**Rationale:**
- Timezone identity is determined by string identifier, not by effective UTC offset
- Two timezones with same offset at a given timestamp are still distinct if their identifiers differ
- This ensures deterministic behavior and prevents hidden semantic equivalence checks

**Examples:**

Example 1: Offset string and IANA ID with same offset
```
Input: "Meeting at 14:00 UTC+2"
Source timezone: "+02:00"
Channel default: "Europe/Amsterdam"  # UTC+2 in January

DisplayBlock entries:
- Entry 1: timezone="+02:00", local_time="14:00"
- Entry 2: timezone="Europe/Amsterdam", local_time="14:00"

Both entries displayed (different identifiers, even though offset is same)
```

Example 2: Multiple IANA IDs with same offset
```
Source: "Europe/Amsterdam"  # UTC+1/UTC+2 with DST
Active: ["Europe/Berlin"]  # UTC+1/UTC+2 with DST (same offset in winter)

DisplayBlock entries:
- Entry 1: timezone="Europe/Amsterdam", local_time="14:00"
- Entry 2: timezone="Europe/Berlin", local_time="14:00"

Both entries displayed (different identifiers, even though offset is same)
```

**Note:** This behavior is intentional and aligns with the Timezone Identity Model (see §Timezone Identity Model above).

**Ordering rules:**
- `entries` must be ordered according to `ordering` strategy
- Order is determined by core processor
- Adapter must preserve order when formatting

**Notes:**
- `ambiguous` is informational; if truly ambiguous, core returns None instead
- Adapter uses `ordering` to verify output order matches expectation

**partial flag semantics:**

`partial = true` iff:
- count of **unique** candidate timezones
  (base + channel default + active_timezones, deduplicated by string identity)
  > max_timezones

Meaning:
Some candidates were omitted due to display limit (truncation).

**Important:** Candidates are deduplicated before counting. If `base_timezone == channel_default_timezone`, they count as 1, not 2. This ensures `partial` reflects actual output truncation, not theoretical candidate count.

**Critical edge case: Partial conversion failures**

If some timezones fail to convert (e.g., invalid IANA ID, conversion errors):
- Failed conversions are excluded from `displayed entries`
- `partial` still reflects truncation only
- Conversion failures do NOT affect `partial`

**Examples:**

Example 1: All slots filled, some candidates omitted
```
total_candidates = 6 (source + 5 active_timezones)
max_timezones = 5
All 6 candidates convert successfully
displayed_entries = 5 (first 5 by priority)
partial = true (1 timezone omitted due to limit)
```

Example 2: Conversion failures, truncation still applies
```
total_candidates = 6 (source + 5 active_timezones)
max_timezones = 5
3 candidates fail conversion (invalid IANA IDs)
displayed_entries = 3 (only successful conversions)
partial = true (candidates exceeded limit regardless of failures)
```

Example 3: No limit reached
```
total_candidates = 3 (source + 2 active_timezones)
max_timezones = 5
All 3 candidates convert successfully
displayed_entries = 3
partial = false (no limit reached, all candidates displayed)
```

Example 4: Edge case - exactly max_timezones candidates, all succeed
```
total_candidates = 5 (source + 4 active_timezones)
max_timezones = 5
All 5 candidates convert successfully
displayed_entries = 5
partial = false (no candidates omitted, limit not exceeded)
```

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

**Note on `default_timezone`:**
- Both `null` and the string `"UTC"` are treated as system UTC fallback
- When `default_timezone = null` or `default_timezone = "UTC"`, resolver interprets it as `"UTC"` (see POLICIES.md §68-72)
- This provides flexibility: users can specify either `null` or `"UTC"` in configuration, both result in UTC fallback behavior
- Example: `default_timezone: null` and `default_timezone: "UTC"` are equivalent

**Mapping from configuration.yaml:**
- `core.max_time_mentions` → `CoreConfig.max_time_mentions`
- `core.default_timezone` → `CoreConfig.default_timezone` (optional, defaults to null = UTC)
- `output.max_timezones` → `CoreConfig.max_timezones`
- `output.ordering` → `CoreConfig.ordering`

---

## CityIndex

**Type:** `Mapping[str, str]` — lowercase name/alias → IANA timezone ID

**Purpose:** Pre-built lookup table for city-to-timezone resolution.

**Construction:** See TIMEZONE_EXTRACTION_RULES.md §2.1

**Why passed as argument:**
- Core cannot load files (Invariant #2)
- Adapter owns `cities.json` and builds index at startup
- Passing as argument maintains core purity (Invariant #7)

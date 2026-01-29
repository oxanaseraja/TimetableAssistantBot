# CORE_CONTRACT.md — Core Invocation Interface (MVP)

This document defines how adapters invoke the core.

---

## CoreProcessor Interface

```python
def process(
    event: CoreMessageEvent,
    user_profile: UserProfile,
    channel_context: ChannelContext,
    city_index: Mapping[str, str],
    config: CoreConfig
) -> DisplayBlock | None
```

**Arguments:**
- `event` — the message to process
- `user_profile` — timezone info for message author (may have null timezone)
- `channel_context` — channel default and active timezones
- `city_index` — pre-built city→timezone lookup table (from cities.json)
- `config` — processing configuration (limits, ordering, defaults)

**Returns:**
- `DisplayBlock` — formatted output for adapter to render
- `None` — no output (no time detected, ambiguity, suppression)

**Why 5 arguments:**
- Core cannot access files (Invariant #2) → city_index passed in
- Core cannot have global config (Invariant #7) → config passed in
- All data explicitly passed = pure function = testable in isolation

---

## Rules

1. **Synchronous call** — no async, no callbacks
2. **Pure function** — no side effects, no I/O, no storage access
   - **Exception:** Core modules may use Python's standard `logging` module for debug/info/warning messages. This does not affect function purity or deterministic behavior. Logging should remain only for monitoring and debugging purposes, without changing function state.
3. **Deterministic** — same inputs always produce same output
4. **Never raises exceptions** — all errors result in `None`

---

## Data Flow

```
Adapter loads at startup:
  - city_index (from cities.json)
  - config (from configuration.yaml)

Adapter constructs per message:
  - CoreMessageEvent (from platform event)
  - UserProfile (from users.json lookup)
  - ChannelContext (from users.json lookup)

Adapter calls:
  result = process(event, user_profile, channel_context, city_index, config)

Adapter handles result:
  - if result is None → send nothing
  - if result is DisplayBlock → format and send
```

---

## Critical Constraints

- **Core does not know where data comes from**
- **Core has no access to storage or files**
- **Core is deterministic from all five arguments only**
- **Adapter is responsible for constructing all inputs**
- **city_index and config are loaded once at startup, reused for all messages**

This ensures core is testable in complete isolation.

---

## Adapter Obligations

- If `None`, send nothing
- Adapter never formats without a `DisplayBlock`
- Adapter must catch any unexpected exceptions (defensive)

---

## Resolver Responsibilities

**Timezone resolution layer boundaries:**

The resolver (`resolve_timezone`) is responsible for:
- Selecting timezone source according to priority rules (see `POLICIES.md` §3)
- Determining resolution source (`EXPLICIT_HINT`, `USER_PROFILE`, etc.)
- Detecting ambiguity when multiple sources conflict
- Interpreting `config.default_timezone = null` as `"UTC"` (single source of truth for fallback timezone resolution)

The resolver is **NOT responsible for**:
- Validating timezone format (IANA vs offset)
- Checking if timezone ID exists in `zoneinfo.available_timezones()`
- Normalizing timezone strings

**Why:**
- Resolver works with "signals" (abstract timezone identifiers)
- Format validation is responsibility of converter
- This separation maintains clean pipeline: extractor → resolver → converter
- Prevents duplicate validation logic
- Simplifies testing (each layer tested independently)

**Behavior:**
- Resolver passes `explicit_timezone` to converter as-is (no format checks)
- Converter validates format and handles both IANA IDs and offset strings
- If converter receives invalid format → conversion fails gracefully (see Partial Failure Handling)

**Offset strings as base_timezone:**
- Offset strings (e.g., `"+03:00"`) can be resolved as `base_timezone` when extracted from message text
- When offset string is resolved as `base_timezone`:
  - It is included in `target_timezones` for conversion (same as IANA IDs)
  - Converter handles it as fixed-offset timezone (no DST)
  - It appears in DisplayBlock with offset string as `timezone_id` (not converted to IANA ID)
- This maintains consistency: explicit hints (including offsets) bypass user/channel timezone resolution

---

## Target Timezone List Construction

**See also:** `CONTRACTS.md` §Timezone Identity Model for identity rules.

**Algorithm:**

The processor builds a prioritized list of target timezones for conversion:

1. **Source timezone** (always first)
   - The `base_timezone` from `ResolvedTimeContext`
   - This is where the original time was expressed

2. **Channel default timezone** (second priority, if different from source)
   - From `ChannelContext.default_timezone`
   - Only added if it differs from source timezone by string identity

3. **Active timezones** (remaining slots, up to `max_timezones` limit)
   - From `ChannelContext.active_timezones`
   - Added in order until `max_timezones` limit is reached

**Deduplication rule:**

After building the candidate timezone list, the system removes duplicates according to the following identity rule:

- **Deduplication is performed by exact string identity of timezone identifiers**
- **No semantic equivalence by offset is applied**

**Examples:**

Example 1: Different string identifiers (not deduplicated)
```
Source: "+02:00"
Channel default: "Europe/Amsterdam"
Result: ["+02:00", "Europe/Amsterdam"]  # Both included (different strings)
```

Example 2: Same string identifier (deduplicated)
```
Source: "Europe/Amsterdam"
Channel default: "Europe/Amsterdam"
Result: ["Europe/Amsterdam"]  # Duplicate removed (same string)
```

Example 3: Offset string vs IANA ID with same offset (not deduplicated)
```
Source: "+02:00"
Active timezones: ["Europe/Amsterdam"]  # UTC+2 in January
Result: ["+02:00", "Europe/Amsterdam"]  # Both included (different strings)
```

**Rationale:**
- String identity is deterministic and unambiguous
- No hidden heuristics or semantic equivalence checks
- Prevents DST-related confusion (offset strings vs IANA IDs behave differently)
- Simple to implement and test

---

## UTC Offset Formatting (Converter)

**Requirement:** The converter must return `utc_offset` (in `ConvertedTime`) strictly in `±HH:MM` format. If a valid offset cannot be produced, the timezone is skipped as invalid.

**Rationale:** No fallback values (e.g. fabricating `+00:00`) — preserves determinism and data integrity.

**Algorithm:**
1. Get `offset = target_time.strftime("%z")`
2. If `offset` is empty or length is not 5, skip the timezone.
3. Otherwise compute `offset_formatted = f"{offset[:3]}:{offset[3:]}"` (e.g. `"+0100"` → `"+01:00"`).

**Error handling:** Any conversion error → skip that timezone. Partial failures must not block successful conversions (see §Partial Failure Handling in Converter below).

---

## Partial Failure Handling in Converter

**See also:** §UTC Offset Formatting (Converter) above — invalid or malformed offset → timezone skipped.

**Scenario:** Conversion fails for one or more timezones in the target list.

**Behavior:**
- Failed timezone conversions are skipped
- Successful conversions are still returned
- Partial `DisplayBlock` is created if at least one conversion succeeds
- If all conversions fail → converter returns empty list → core returns `None`

**Examples:**

Example 1: Partial failure - some timezones invalid
```
Target: ["Europe/Amsterdam", "Invalid/TZ", "America/New_York"]
Result: [ConvertedTime(Europe/Amsterdam), ConvertedTime(America/New_York)]
Behavior: Invalid timezone "Invalid/TZ" is silently skipped
DisplayBlock: Created with 2 entries, partial flag depends on total_candidates
```

Example 2: All timezones invalid
```
Target: ["Invalid1/TZ", "Invalid2/TZ"]
Result: []
Behavior: All conversions failed
DisplayBlock: None (core returns None, no reply sent)
```

Example 3: Mixed valid/invalid with offset strings
```
Target: ["+03:00", "Invalid/TZ", "Europe/London", "Invalid2/TZ"]
Result: [ConvertedTime(+03:00), ConvertedTime(Europe/London)]
Behavior: Invalid IANA IDs skipped, valid offset and IANA ID converted
DisplayBlock: Created with 2 entries
```

Example 4: Invalid offset string
```
Target: ["+15:00", "Europe/Amsterdam"]  # +15:00 is out of range [0, 14]
Result: [ConvertedTime(Europe/Amsterdam)]
Behavior: Invalid offset "+15:00" skipped (out of range), valid IANA ID converted
DisplayBlock: Created with 1 entry
```

**Rationale:**
- Graceful degradation: show available timezones even if some fail
- Better UX than failing completely
- Invalid timezones may be configuration errors, shouldn't break entire response

---

## Invalid base_timezone Handling

**Scenario:** `base_timezone` from `ResolvedTimeContext` is invalid (invalid offset string or invalid IANA ID).

**Behavior:**
- Converter validates `base_timezone` format and range
- If `base_timezone` is an invalid offset string (out of range [0, 14] hours, [0, 59] minutes) → converter returns empty list `[]`
- If `base_timezone` is an invalid IANA ID (not in `zoneinfo.available_timezones()`) → converter returns empty list `[]`
- If converter returns empty list → core processor returns `None` → adapter sends no reply

**Why this behavior:**
- Resolver is **NOT responsible** for validating timezone format (see Resolver Responsibilities above)
- Resolver passes `base_timezone` as-is to converter
- Converter validates format and handles errors gracefully
- This separation maintains clean pipeline: extractor → resolver → converter
- Prevents duplicate validation logic

**Examples:**

Example 1: Invalid offset string in base_timezone
```
ResolvedTimeContext.base_timezone: "+15:00"  # Out of range [0, 14]
Converter behavior: Validates range, detects invalid offset
Result: [] (empty list)
Core behavior: Returns None (no reply sent)
```

Example 2: Invalid IANA ID in base_timezone
```
ResolvedTimeContext.base_timezone: "Invalid/TZ"
Converter behavior: zoneinfo.ZoneInfoNotFoundError caught
Result: [] (empty list)
Core behavior: Returns None (no reply sent)
```

Example 3: Valid base_timezone, invalid target timezones
```
ResolvedTimeContext.base_timezone: "Europe/Amsterdam"  # Valid
Target timezones: ["Europe/Amsterdam", "Invalid/TZ", "America/New_York"]
Converter behavior: Converts base_timezone successfully, skips invalid target
Result: [ConvertedTime(Europe/Amsterdam), ConvertedTime(America/New_York)]
Core behavior: Returns DisplayBlock with 2 entries (partial failure handling)
```

**Note:** This is expected behavior. Resolver passes timezone as-is, converter validates and handles errors. This ensures that invalid timezones from any source (explicit hint, user profile, channel default) are caught and handled gracefully.

---

## References

- `CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — how adapter constructs UserProfile
- `ARCHITECTURAL_INVARIANTS.md` — purity constraints
- `TIMEZONE_EXTRACTION_RULES.md` — converter support for offset strings

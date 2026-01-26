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

## Partial Failure Handling in Converter

**Scenario:** Conversion fails for one or more timezones in the target list.

**Behavior:**
- Failed timezone conversions are skipped
- Successful conversions are still returned
- Partial `DisplayBlock` is created if at least one conversion succeeds
- If all conversions fail → converter returns empty list → core returns `None`

**Examples:**
- Target: `["Europe/Amsterdam", "Invalid/TZ", "America/New_York"]`
- Result: `[ConvertedTime(Europe/Amsterdam), ConvertedTime(America/New_York)]`
- Invalid timezone is silently skipped

- Target: `["Invalid1/TZ", "Invalid2/TZ"]`
- Result: `[]` → core returns `None` → no reply

**Rationale:**
- Graceful degradation: show available timezones even if some fail
- Better UX than failing completely
- Invalid timezones may be configuration errors, shouldn't break entire response

---

## References

- `CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — how adapter constructs UserProfile
- `ARCHITECTURAL_INVARIANTS.md` — purity constraints
- `TIMEZONE_EXTRACTION_RULES.md` — converter support for offset strings

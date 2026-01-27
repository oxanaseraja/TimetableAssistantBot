# POLICIES.md — Deterministic Core Rules (MVP)

These policies are authoritative for the platform-agnostic core.
No probabilistic guessing is allowed in MVP.
MVP platform: Telegram.

## Boundary Rule

Core never sees platform identifiers. All platform identity is resolved at adapter boundary.

---

## 1. Time Detection Policy

**Implementation:** Time is parsed by **regex patterns only**.
No LLM interpretation, no heuristics, no guessing.

**Grammar specification:** See `TIME_PARSING_RULES.md` for:
- Supported patterns (regex)
- Unsupported formats
- Parsing algorithm
- Edge cases

**Behavioral rules (this document):**
- If no time pattern matches → no time detected
- If time is ambiguous (bare hour without am/pm) → no reply
- Max 3 time mentions per message (see §6)

**Note:** Dot-separated time format (HH.MM) is explicitly NOT supported in MVP.
Rationale: ambiguity with decimal numbers and version strings.

---

## 2. Timezone Extraction Policy

**Implementation:** Timezone hints are extracted by **exact matching only**.
No fuzzy matching, no inference, no guessing.

**Extraction specification:** See `TIMEZONE_EXTRACTION_RULES.md` for:
- Supported signals (offset, IANA, city)
- Priority order
- Matching algorithm
- cities.json format

**Behavioral rules (this document):**
- First matching signal wins (by priority)
- Unknown city names are ignored
- Abbreviations (EST, CET) are not supported in MVP

---

## 3. Timezone Resolution Precedence

Priority order:
1. `EXPLICIT_HINT` — Explicit offset in text (UTC+2, +0300)
2. `EXPLICIT_HINT` — Explicit timezone name or city (from text)
3. `USER_PROFILE` — User profile timezone
4. `CHANNEL_DEFAULT` — Channel default timezone
5. `ACTIVE_TZ_SINGLE` — If exactly one active timezone → use it
6. `SYSTEM_DEFAULT` — Fallback to UTC (if configured) or ambiguity

**SYSTEM_DEFAULT behavior:**
- Used only when all other sources exhausted
- If `config.default_timezone` is set → use it
- If `config.default_timezone` is null → use UTC
- ResolutionSource is set to `SYSTEM_DEFAULT` in this case

**System Default Timezone Resolution:**
- `config.default_timezone = null` means system UTC (per `CONTRACTS.md`)
- Resolver MUST interpret `null` as `"UTC"` when producing `ResolvedTimeContext.base_timezone`
- Internal representation (`CoreConfig.default_timezone`) MAY use `null`, but resolved context (`ResolvedTimeContext.base_timezone`) MUST always contain a concrete timezone string (IANA ID or offset)
- The interpretation of `null → "UTC"` happens in the resolver layer, which is the single source of truth for fallback timezone resolution

**Note:** Both `null` and the string `"UTC"` in configuration are treated equivalently as system UTC fallback (see `CONTRACTS.md` §CoreConfig for details).

**Examples:**

Example 1: default_timezone = null
```
config.default_timezone = null
No explicit hint, no user/channel timezone
Resolver returns: base_timezone = "UTC", resolution_source = "SYSTEM_DEFAULT"
```

Example 2: default_timezone = "UTC" (equivalent to null)
```
config.default_timezone = "UTC"  # Treated as null during config loading
No explicit hint, no user/channel timezone
Resolver returns: base_timezone = "UTC", resolution_source = "SYSTEM_DEFAULT"
```

Example 3: default_timezone = explicit IANA ID
```
config.default_timezone = "Europe/Amsterdam"
No explicit hint, no user/channel timezone
Resolver returns: base_timezone = "Europe/Amsterdam", resolution_source = "SYSTEM_DEFAULT"
```

---

## 4. Ambiguity Policy (Safe-Only)

MVP never outputs assumed or probabilistic times.

- Exactly one valid interpretation → answer
- Multiple possible interpretations → return None (no reply)
- Missing timezone + >1 active timezone → do not answer
- Missing am/pm in 1–12 → return None

No multiple alternatives in MVP.

Ambiguity behavior (MVP):
- Core returns `None`
- Adapter sends no reply
- Clarification dialogs are out of scope

---

## 4.1 DST Policy

**Core does not infer calendar dates from text.**

All time mentions are interpreted relative to message timestamp date.

Rules:
- Use `timestamp_utc.date()` as reference date for DST calculation
- Cross-day inference is explicitly unsupported
- "Tomorrow at 10" is not parsed (relative time)
- DST transitions are handled by `zoneinfo` automatically

This makes the system predictable and formally bounded.

### DST Fold/Gap Handling

- **Gap (spring forward):** Invalid local times are interpreted as the first valid
  time after the gap (zoneinfo default behavior)

- **Fold (fall back):** Ambiguous local times are interpreted as the first occurrence
  (pre-transition time)

- MVP does not detect or report DST ambiguity explicitly.

---

## 5. Active Timezones Policy

**Source of truth:** `UserProfile.timezone`.

**ActiveTimezoneSet** = all known user timezones present in channel context.

Activity tracking and decay are out of scope for MVP.

**Timezone acquisition (MVP):**
- `UserProfile.timezone` is pre-populated by adapter from `users.json`
- User-facing timezone setup is out of scope
- See `USER_PROFILE_MODEL.md` for details

**Empty active_timezones behavior:**
- If `active_timezones = []` (empty list):
  - No active timezones are included in `target_timezones`
  - Only `source_timezone` and `channel_default_timezone` (if different) are included
  - If no explicit hint, user timezone, or channel default → resolver falls back to `SYSTEM_DEFAULT` (UTC)
  - This is a valid system state and does not cause ambiguity
  - System gracefully handles channels with no known member timezones

---

## 6. Output / Display Policy

**Constraints:**
- Max timezones shown: 5
- Up to 3 time mentions are allowed per message
- One line per timezone with city list
- Stable ordering for tests

**Time mentions limit:**
- Messages with exactly 3 times: processed (first time used in MVP)
- Messages with more than 3 times (4+): ignored entirely (spam suppression)

**Ordering:**
1. Source timezone
2. Channel default (if different)
3. Others by UTC offset (asc), then `timezone_id`

**Spam suppression:**
- One bot reply per user message
- Ignore messages with > 3 time mentions

**Output format:** See `ADAPTER_CONTRACTS.md` §6.

---

## 6.1 Multiple Times in One Message (MVP)

**MVP simplification:** Process only the **first** detected time mention.

Rationale:
- Simplifies DisplayBlock structure (one time = one conversion)
- Reduces complexity of ambiguity resolution
- Avoids mixing timezones from different contexts

**Behavior:**
```
Input: "call at 10am NYC or 2pm London"
Detected: [10am, 2pm]
Processed: 10am only (first by position)
Output: DisplayBlock for 10:00 NYC → other timezones
```

**Future extension (post-MVP):**
- Process all detected times (up to 3)
- Return `List[DisplayBlock]` instead of single block
- Each DisplayBlock represents one time mention

**Note:** Parser still returns up to 3 times (for future use), but processor uses only `detected_times[0]` in MVP.

---

## 7. Edit / Lifecycle Policy

Supported events (MVP):
- New message
- Message edit
- Message delete (no retroactive cleanup)

Rules:
- New message with time → parse → resolve → respond
- Edit removing time → delete previous reply (if exists)
- Edit changing time → recompute and update

Implementation: See `ADAPTER_CONTRACTS.md` §4 (reply_mapping).

---

## 8. Telegram Adapter Rules (MVP)

These rules are adapter-specific and do not affect core logic.

**ID mapping (deterministic):**
- `internal_user_id` = `sha256(f"telegram:{platform_user_id}")`
- `internal_channel_id` = `sha256(f"telegram:{platform_chat_id}")`
- `internal_message_id` = `sha256(f"{platform_chat_id}:{platform_message_id}")`

**Suppress duplicates:**
- Duplicate = same `internal_message_id` already processed
- Adapter keeps in-memory `processed_message_ids`
- If `is_edit=True`, allow reprocessing even if seen before

**Cities in output (MVP):**
- Adapter populates `cities` from local city list
- Cities grouped by timezone, sorted alphabetically

---

## References

- `TIME_PARSING_RULES.md` — time grammar (input contract)
- `TIMEZONE_EXTRACTION_RULES.md` — timezone extraction rules
- `USER_PROFILE_MODEL.md` — user data source
- `ADAPTER_CONTRACTS.md` — adapter runtime contract
- `ARCHITECTURAL_INVARIANTS.md` — system invariants

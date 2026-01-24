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
1. Explicit offset in text (UTC+2, +0300)
2. Explicit timezone name or city (from text)
3. User profile timezone
4. Channel default timezone
5. If exactly one active timezone → use it
6. Otherwise → ambiguity (no reply)

System default UTC is used only if channel has no active timezones and no defaults.

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

---

## 5. Active Timezones Policy

**Source of truth:** `UserProfile.timezone`.

**ActiveTimezoneSet** = all known user timezones present in channel context.

Activity tracking and decay are out of scope for MVP.

**Timezone acquisition (MVP):**
- `UserProfile.timezone` is pre-populated by adapter from `users.json`
- User-facing timezone setup is out of scope
- See `USER_PROFILE_MODEL.md` for details

---

## 6. Output / Display Policy

**Constraints:**
- Max timezones shown: 5
- Max time mentions processed: 3
- One line per timezone with city list
- Stable ordering for tests

**Ordering:**
1. Source timezone
2. Channel default (if different)
3. Others by UTC offset (asc), then `timezone_id`

**Spam suppression:**
- One bot reply per user message
- Ignore messages with > 3 time mentions

**Output format:** See `ADAPTER_CONTRACTS.md` §6.

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

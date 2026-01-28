# Specification Freeze — Timetable Assistant Bot (MVP)

Status: Frozen (Handover-ready)  
Version: v1.0.2 final  
Date: 2026-01-28  
Scope: MVP core + Telegram adapter  

This document fixes the behavioral and architectural specification of the MVP.

---

## Revision History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-27 | v1.0 | Initial freeze | — |
| 2026-01-28 | v1.0.1 | Clarified §9.3 "last match" for duplicate cities; added distance tie-breaker to §2.4; clarified §9.2 cities.json validation | — |
| 2026-01-28 | v1.0.2 final | Closed Decision D-001 (compact offsets rejected); final verification completed; handover-ready status | — |

After this point, behavior-changing modifications are considered out of scope unless explicitly approved as v2.

**Canonical source documents:** This freeze captures behavioral contracts only. For structural definitions and detailed algorithms, refer to:
- `CONTRACTS.md` — DTO definitions and data structures
- `POLICIES.md` — deterministic core rules
- `CORE_CONTRACT.md` — core invocation interface
- `TIMEZONE_EXTRACTION_RULES.md` — extraction algorithms
- `TIME_PARSING_RULES.md` — parsing grammar

---

## 1. Purpose of Spec Freeze

The original product brief intentionally contains underspecified areas and open design space.

During implementation and formal verification, multiple implicit policies and architectural decisions were discovered and resolved.

The goal of this freeze is to:

- Lock all externally observable behavior  
- Fix architectural invariants  
- Prevent uncontrolled scope creep  
- Separate *correctness-critical* decisions from *future improvements*  

After this freeze:

- No new parsing rules  
- No new resolution strategies  
- No changes in ordering, priority, or fallback policies  
- No changes in error handling semantics  

---

## 2. Frozen Architectural Invariants

The following invariants are considered fundamental and must not be violated by future changes.

### 2.1 Core Stability Invariants

- Core never raises uncaught exceptions  
- Any internal error results in `None` output  
- Core is deterministic for identical input  

**Immutability requirement:**
- All core DTOs are frozen dataclasses  
- `DisplayBlock.entries` is `Tuple[Entry, ...]` (not mutable list)  
- `DisplayFlags` is a frozen dataclass  
- Collection fields in **core inputs and resolution state** use immutable types (`Tuple`, not `List`) to ensure full immutability  
- Presentation-layer fields populated by adapters (e.g., `Entry.cities`) may use mutable collections  

### 2.2 Parsing Invariants

- Time mentions are detected using explicit regex rules  
- Overlapping matches are resolved by priority and length rules  
- 12-hour format with AM/PM has priority over 24-hour format  
- No implicit guessing of missing AM/PM  

### 2.3 Extraction Invariants

- Timezone signals are extracted only from:
  - Explicit IANA identifiers  
  - Explicit UTC offsets  
  - City names from `cities.json`  

- No implicit geo inference  
- No user location inference  

**Context window:**
- Timezone hints are searched within ±30 characters from time mention  
- Window is measured from the **start position** of the time mention (not center or end)  
- Formula: `start = max(0, time_position - 30)`, `end = min(len(text), time_position + 30)`  

**City extraction priority:**
- Multi-word phrases (2-3 words) are preferred over single-word matches when overlapping at the same start position  
- Longer phrase match takes precedence (e.g., "New York" wins over "New")  

### 2.4 Resolution Invariants

- Closest-signal resolution by distance  
- Fixed priority order:
  1. Explicit offset  
  2. IANA timezone  
  3. City  
  4. User profile  
  5. Channel default timezone  
  6. Active timezones (if unique)  
  7. System default ("UTC")  

- Priority wins over distance when equal  
- **Distance tie-breaker:** if multiple signals of the same priority have equal distance to time mention, the first by text position (left-to-right) is selected  

### 2.5 Conversion Invariants

- All conversions are based on timezone-aware datetime  
- No artificial fallback offsets are introduced  
- Invalid timezone → conversion skipped  

---

## 3. Frozen Behavioral Contracts

These contracts define externally observable behavior.

### 3.1 Message Processing

- Maximum number of processed time mentions: `max_time_mentions`  
- Maximum number of resolved timezones: `max_timezones`  
- If timezone candidates exceed `max_timezones` → `partial=True`  

MVP processes only the first detected time mention in a message.  
Additional time mentions are ignored in v1.  
Multi-time support is explicitly deferred to v2+.  

**partial flag semantics:**

- `partial=True` indicates that **timezone candidates** exceeded `max_timezones` limit  
- `partial` is determined **only** by `max_timezones`, **not** by `max_time_mentions`  
- `partial` does not reflect conversion failures  
- `partial` depends only on timezone truncation, not on successful conversions  

**time_mentions_truncated (diagnostic only):**

- If detected time mentions exceed `max_time_mentions`, this is logged for diagnostics  
- This does **not** affect `partial` flag — `partial` is exclusively for timezone truncation  
- Implementation may log: `"mentions_truncated={time_mentions_truncated}"`  
- This is an internal diagnostic, not exposed in `DisplayBlock`  

Messages exceeding these limits are partially processed, never rejected.

---

### 3.2 Output Formatting

- Each timezone appears at most once in output  
- No duplicate cities within one timezone  
- Ordering:
  1. Source timezone first  
  2. Channel default timezone (if different from source)  
  3. Remaining timezones sorted by UTC offset (ascending)  
  4. Stable ordering inside equal offsets (deterministic by timezone ID)  

**Deduplication rule:**
- After UTC normalization (e.g., `"+00:00"` → `"UTC"`), timezone IDs are deduplicated  
- First occurrence per priority order is retained  
- Deduplication uses exact string identity (no semantic equivalence by offset)  

---

### 3.3 UTC Representation

- UTC is represented as IANA ID `"UTC"`  
- Offset `+00:00` is not used for display  
- Offset string `"+00:00"` is normalized to `"UTC"` before deduplication  
- IANA IDs with effective offset +00:00 (e.g., `"Europe/London"` in winter) retain their original ID  

---

### 3.4 Error Handling Policy

- Invalid time mention → skipped  
- Invalid timezone signal → skipped  
- Invalid cities.json entry → skipped  
- No user-visible error messages  
- Bot remains silent on malformed input  

**Message deletion behavior:**
- No retroactive cleanup of bot replies if original message is deleted  
- Telegram API does not notify bots about message deletions in group chats  
- Orphaned bot replies remain in chat (acceptable in MVP)  
- `reply_mapping` entry remains until FIFO eviction  

---

## 4. Frozen Configuration Semantics

### 4.1 Required Configuration

The following parameters are mandatory for adapter startup:

- telegram.token  
- telegram.chat_id  
- data.cities_path  
- data.users_path  

Missing required parameters → adapter does not start (fail-fast)

**Data file error handling:**

| File | Condition | Behavior |
|------|-----------|----------|
| `configuration.yaml` | Invalid YAML syntax | Adapter does not start (fatal) |
| `cities.json` | Invalid JSON syntax | Adapter does not start (fatal) |
| `cities.json` | Missing file | Adapter does not start (fatal) |
| `cities.json` | Empty `[]` | Valid state, city extraction disabled |
| `cities.json` | Duplicate city/alias keys | Last entry wins, warning logged |
| `cities.json` | Invalid timezone in entry | Entry skipped, warning logged |
| `users.json` | Invalid JSON syntax | Adapter does not start (fatal) |
| `users.json` | Missing file | Treated as empty `{}`, adapter starts |
| `users.json` | Invalid structure (not dict) | Treated as empty `{}`, warning logged |

**Note:** Adapter retry policy (retry_attempts, backoff) is frozen per `ADAPTER_CONTRACTS.md` §2.

---

### 4.2 Optional Configuration

- core.default_timezone is allowed only as final system fallback  
- It does not participate in normal resolution unless no other signals are available  

Any future configurability beyond fallback requires spec version bump.

**Configuration validation:**
- Invalid integer values → use default, log warning  
- Invalid ordering value → use `"SOURCE_FIRST"`, log warning  
- Invalid IANA timezone ID → treat as `null` (UTC), log warning

---

## 5. Frozen Limits and Performance Guards

To prevent pathological cases:

- Maximum input message length: 4096 characters  
- Maximum processed time mentions: fixed by config  
- Maximum timezone candidates: fixed by config  

Regex processing is bounded by these limits.

---

## 6. Out of Scope After Freeze

The following features are explicitly excluded from MVP:

- Natural language date parsing  
- Relative times ("in two hours", "tomorrow")  
- Automatic user timezone inference  
- Multiple source timezones in one sentence  
- Multiple time mentions per message  
- Cross-message context  

These are considered v2+ features.

---

## 7. Allowed Changes After Freeze

The following changes are allowed without version bump:

### 7.1 Non-behavioral Changes

- Refactoring  
- Internal performance optimizations  
- Logging improvements  
- Type annotation improvements  

### 7.2 Test Extensions

- New test cases  
- Edge case coverage  
- Unicode coverage  

### 7.3 Documentation Clarifications

- Additional examples  
- Policy explanations  
- Error handling notes  

---

## 8. Disallowed Changes After Freeze

The following require a new spec version:

- Changing parsing priorities  
- Adding new time formats  
- Changing resolution strategy  
- Changing fallback policies  
- Changing output ordering  
- Changing error handling semantics  

---

## 9. Known Open Design Decisions (Accepted)

The following unresolved aspects are consciously accepted in MVP:

1. Very long messages are truncated by upstream platform  
2. cities.json: invalid entries are skipped with warning (structural validation), but semantic correctness (correct timezone for city) is operator's responsibility  
3. cities.json: `country` is optional metadata and does not participate in extraction or resolution  
4. Ambiguous city names are resolved by last match in dataset  
5. No disambiguation UI is provided  
6. No retroactive cleanup of bot replies when original message is deleted  
7. Orphaned replies from deleted messages remain in chat until manual cleanup  

These are documented limitations, not bugs.

---

## 10. Freeze Rationale

This freeze reflects a stable architecture satisfying:

- Deterministic behavior  
- Closed invariants  
- Fully specified external contracts  
- Bounded performance  

Remaining open points are either:

- UX decisions  
- Future product features  
- Non-critical improvements  

At this point, the MVP is considered:

**Architecturally closed, behaviorally stable, and ready for handover.**

---

## 11. References

This freeze document captures behavioral contracts. For detailed specifications, consult:

| Document | Purpose |
|----------|---------|
| `CONTRACTS.md` | DTO definitions, data structures, type contracts |
| `POLICIES.md` | Deterministic core rules, resolution precedence |
| `CORE_CONTRACT.md` | Core invocation interface, partial failure handling |
| `TIMEZONE_EXTRACTION_RULES.md` | Extraction algorithms, normalization rules |
| `TIME_PARSING_RULES.md` | Parsing grammar, regex patterns |
| `ARCHITECTURAL_INVARIANTS.md` | System invariants (23 total) |
| `ADAPTER_CONTRACTS.md` | Adapter runtime contract, error handling |
| `USER_PROFILE_MODEL.md` | User/channel data model |

---

## Decision D-001: Compact UTC offsets without colon

Status: CLOSED  
Scope: TIMEZONE_EXTRACTION_RULES  
Decision:
- Compact offsets of form +HHMM are NOT supported.
- Only +HH or +HH:MM are supported.
- Example "+0300" is invalid and removed; previous behavior was coincidental.

Rationale:
- Avoid ambiguous parsing
- Match documented regex behavior


End of document.

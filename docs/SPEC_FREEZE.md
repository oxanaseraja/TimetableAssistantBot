# Specification Freeze — Timetable Assistant Bot (MVP)

Status: Frozen  
Version: v1.0  
Date: 2026-01-27  
Scope: MVP core + Telegram adapter  

This document fixes the behavioral and architectural specification of the MVP.
After this point, behavior-changing modifications are considered out of scope unless explicitly approved as v2.

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

### 2.5 Conversion Invariants

- All conversions are based on timezone-aware datetime  
- No artificial fallback offsets are introduced  
- Invalid timezone → conversion skipped  

---

## 3. Frozen Behavioral Contracts

These contracts define externally observable behavior.

### 3.1 Message Processing

- Maximum number of processed time mentions: `max_times`  
- Maximum number of resolved timezones: `max_timezones`  
- If candidates exceed limit → `partial=True`  

MVP processes only the first detected time mention in a message.  
Additional time mentions are ignored in v1.  
Multi-time support is explicitly deferred to v2+.  

partial flag semantics:

- partial=True indicates that candidates exceeded configured limits  
- partial does not reflect conversion failures  
- partial depends only on truncation, not on successful conversions  

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

---

### 3.3 UTC Representation

- UTC is represented as IANA ID `"UTC"`  
- Offset `+00:00` is not used for display  

---

### 3.4 Error Handling Policy

- Invalid time mention → skipped  
- Invalid timezone signal → skipped  
- Invalid cities.json entry → skipped  
- No user-visible error messages  
- Bot remains silent on malformed input  

---

## 4. Frozen Configuration Semantics

### 4.1 Required Configuration

The following parameters are mandatory for adapter startup:

- telegram.token  
- telegram.chat_id  
- data.cities_path  
- data.users_path  

Missing required parameters → adapter does not start (fail-fast)

---

### 4.2 Optional Configuration

- core.default_timezone is allowed only as final system fallback  
- It does not participate in normal resolution unless no other signals are available  

Any future configurability beyond fallback requires spec version bump.

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
2. cities.json correctness is assumed, not enforced strictly  
3. Ambiguous city names are resolved by first match in dataset  
4. No disambiguation UI is provided  

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

End of document.

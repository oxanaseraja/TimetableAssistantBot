# ARCHITECTURAL_INVARIANTS.md — System Invariants

These invariants are **absolute constraints** that must hold at all times.
Any code that violates these invariants is incorrect by definition.

---

## Core Invariants

### 1. Core is pure and deterministic

Core functions have no side effects.
Same input always produces same output.
No randomness, no timestamps from system clock.

**Determinism includes:**
- No dependence on iteration order of hash-based structures
- No locale-dependent formatting
- No floating-point time arithmetic

### 2. Core never performs IO

Core does not:
- Read files
- Write files
- Make network requests
- Access databases
- Log to external systems

All IO happens in adapters.

### 3. Core never accesses storage

Core receives all data as function arguments:
- `CoreMessageEvent`
- `UserProfile`
- `ChannelContext`

Core never queries or modifies persistent state.

### 4. Core never infers missing information

If information is missing, core does not guess.
Missing timezone → ambiguity → no reply.
Missing am/pm → ambiguity → no reply.

### 5. All ambiguity leads to no reply

Core returns `None` for any ambiguous situation.
Adapter sends nothing when core returns `None`.
No "best guess" behavior in MVP.

### 6. Core inputs are immutable

**Core must not mutate any input object.**
All inputs are treated as immutable.
If transformation is needed, create new objects.

### 7. Core has no global state

**Core must not use global or module-level state.**
All state must be passed explicitly as arguments.
No caching, no counters, no debug flags at module level.

### 8. Core never raises uncaught exceptions

**Core must never raise uncaught exceptions.**
All failure conditions are represented by returning `None`.
No `raise` statements that can propagate to adapter.

---

## Adapter Invariants

### 9. Adapters are the only source of side effects

All IO, storage, and external communication happens in adapters.
Adapters are responsible for:
- Receiving platform events
- Loading configuration and data files
- Sending replies
- Persisting state (optional)

### 10. Adapters never modify core logic

Adapters transform data, not behavior.
Business rules live in core, not adapters.

### 11. Adapter runs in asyncio event loop

`python-telegram-bot` v20+ is async.
All IO happens during startup or in event handlers.
Core functions are called synchronously from async handlers.

### 12. Adapter suppresses all core errors

**Adapter must catch and suppress all exceptions from core.**
No user-visible error messages in MVP.
Errors are logged, but user sees nothing.

---

## Parsing Invariants

### 13. Time parsing is regex-based only

No NLP. No LLM. No heuristics.
Only patterns defined in `TIME_PARSING_RULES.md` are recognized.
Unrecognized formats are silently ignored.

### 14. Parser never normalizes input

**Parser must not normalize, rewrite, or reinterpret input text.**
Only exact matches of defined patterns are accepted.
No `10.30 → 10:30` conversion.
No "half past 10" interpretation.

### 15. Timezone extraction is whitelist-based only

Only cities in `cities.json` are recognized.
Only IANA timezone IDs are recognized.
Only UTC/GMT offsets are recognized.
No fuzzy matching. No inference.

### 16. Multiple timezone candidates = ambiguity

**If more than one valid timezone candidate is extracted → ambiguity → `None`.**
No priority rules apply unless explicitly defined in `TIMEZONE_EXTRACTION_RULES.md`.

---

## Data Invariants

### 17. Core never sees platform identifiers

All platform IDs are hashed before reaching core.
Core works with `internal_*_id` only.

### 18. Configuration is immutable at runtime

No hot-reload of configuration.
Changes require restart.

---

## Specification Invariants

### 19. Spec directory is immutable during implementation

`spec/` is read-only during code generation.
Implementation must not modify any file in `spec/`.
All changes to spec are architectural decisions, not implementation fixes.
If spec is incomplete → stop and report missing contract.

---

## Behavioral Invariants

### 20. One reply per user message

Bot sends at most one reply per incoming message.
No follow-up messages. No corrections.

### 21. Silence is acceptable

Not replying is a valid behavior.
Ambiguity → silence.
No time detected → silence.
Error → silence (log only).

---

## Testing Invariants

### 22. Core is testable in isolation

Core can be tested without:
- Network
- Database
- Platform SDK
- Real time

All inputs are mockable.

### 23. Determinism enables golden tests

Same input → same output.
Golden test cases can be version-controlled.
No flaky tests from timing or randomness.

---

## Summary: 23 Invariants

| # | Invariant | Category |
|---|-----------|----------|
| 1 | Core is pure and deterministic | Core |
| 2 | Core never performs IO | Core |
| 3 | Core never accesses storage | Core |
| 4 | Core never infers missing information | Core |
| 5 | All ambiguity leads to no reply | Core |
| 6 | Core inputs are immutable | Core |
| 7 | Core has no global state | Core |
| 8 | Core never raises uncaught exceptions | Core |
| 9 | Adapters are the only source of side effects | Adapter |
| 10 | Adapters never modify core logic | Adapter |
| 11 | Adapter runs in asyncio event loop | Adapter |
| 12 | Adapter suppresses all core errors | Adapter |
| 13 | Time parsing is regex-based only | Parsing |
| 14 | Parser never normalizes input | Parsing |
| 15 | Timezone extraction is whitelist-based only | Parsing |
| 16 | Multiple timezone candidates = ambiguity | Parsing |
| 17 | Core never sees platform identifiers | Data |
| 18 | Configuration is immutable at runtime | Data |
| 19 | Spec directory is immutable | Spec |
| 20 | One reply per user message | Behavioral |
| 21 | Silence is acceptable | Behavioral |
| 22 | Core is testable in isolation | Testing |
| 23 | Determinism enables golden tests | Testing |

---

## References

- `ARCHMINI.md` — system overview
- `POLICIES.md` — behavioral rules
- `DESIGN_CHOICES.md` — rationale for decisions
- `LLM_EXECUTION_PROTOCOL.md` — execution rules

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

**Exception:** Core modules may use Python's standard `logging` module for debug/info/warning messages. This does not affect function purity or deterministic behavior. Logging should remain only for monitoring and debugging purposes, without changing function state.

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

### 7. Core has no mutable global state

**Core must not use mutable global or module-level state.**
All runtime data must be passed explicitly as arguments.
No caching, no counters, no debug flags at module level.

**Allowed (immutable):**
- Compiled regex patterns (`re.compile(...)`)
- Frozen sets (`frozenset(...)`)
- Constants (`MAX_TIMES = 3`)
- Type definitions

**Forbidden (mutable):**
- Module-level dicts or lists that could be modified
- Singleton instances
- Global configuration objects
- Any state that changes between calls

### 8. Core never raises uncaught exceptions

**Core must never raise uncaught exceptions.**
All failure conditions are represented by returning `None`.
No `raise` statements that can propagate to adapter.

**Implementation pattern:**
```python
def process(...) -> DisplayBlock | None:
    try:
        # ... processing logic ...
        return display_block
    except Exception:
        return None  # Any error → silence
```

**Common exception sources to guard:**
- `zoneinfo.ZoneInfo()` → `ZoneInfoNotFoundError`
- `int()` parsing → `ValueError`
- Dict access → `KeyError`

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

**Implementation pattern (REQUIRED):**
```python
async def on_message(update: Update):
    # ... prepare inputs ...
    
    try:
        display = process(event, user_profile, channel_context, city_index, config)
    except Exception as exc:
        logging.error("Core error: %s", exc, exc_info=True)
        display = None  # Suppress error, treat as no output
    
    if display is None:
        return  # No reply
    
    # ... send reply ...
```

**This is not optional.** Even if Invariant #8 guarantees core won't raise,
adapter must still wrap the call defensively (defense in depth).

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

### 16. Timezone resolution follows priority order

Timezone extraction uses **priority order** defined in `TIMEZONE_EXTRACTION_RULES.md`:
1. UTC/GMT offset (highest)
2. IANA timezone ID
3. City name (lowest)

**Rules:**
- Higher priority signal always wins over lower priority
- Within same priority level: closest to time mention wins
- This is NOT ambiguity — it's deterministic resolution

**Ambiguity occurs only when:**
- No timezone signal found AND multiple active_timezones exist
- Time format is genuinely ambiguous (e.g., bare hour without AM/PM)

See `TIMEZONE_EXTRACTION_RULES.md` §4 for full disambiguation rules.

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

`docs/` is read-only during code generation.
Implementation must not modify any file in `docs/`.
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
| 7 | Core has no mutable global state | Core |
| 8 | Core never raises uncaught exceptions | Core |
| 9 | Adapters are the only source of side effects | Adapter |
| 10 | Adapters never modify core logic | Adapter |
| 11 | Adapter runs in asyncio event loop | Adapter |
| 12 | Adapter suppresses all core errors | Adapter |
| 13 | Time parsing is regex-based only | Parsing |
| 14 | Parser never normalizes input | Parsing |
| 15 | Timezone extraction is whitelist-based only | Parsing |
| 16 | Timezone resolution follows priority order | Parsing |
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

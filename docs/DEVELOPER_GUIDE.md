# Developer Guide — Practical Guidelines for Team

This document provides practical guidelines for developers working on the TimetableAssistantBot project.

---

## Logging in Core Modules

### Policy

Core modules may use Python's standard `logging` module for debug/info/warning messages. This does not affect function purity or deterministic behavior.

### Guidelines

1. **Purpose:** Logging in core modules should remain only for monitoring and debugging purposes, without changing function state.

2. **What to log:**
   - Debug messages for troubleshooting (e.g., "Message truncated: exceeds max_time_mentions limit")
   - Warning messages for invalid input handling (e.g., "Invalid timezone ID, skipping")
   - Info messages for important state changes (e.g., "Failed to convert X timezone(s)")

3. **What NOT to log:**
   - Do not log sensitive user data
   - Do not log excessive detail that would impact performance
   - Do not use logging as a way to change function behavior

4. **Best practices:**
   - Use appropriate log levels (`logger.debug()`, `logger.info()`, `logger.warning()`)
   - Keep log messages concise and informative
   - Do not rely on logging for business logic decisions
   - Remember: logging does not affect function determinism or purity

### Rationale

- Logging through Python's standard `logging` module does not affect function purity because:
  - It does not change the return value of functions
  - It does not modify function state
  - Same inputs still produce same outputs (determinism preserved)
  - It's useful for debugging and monitoring in production environments

### Example

```python
import logging

logger = logging.getLogger(__name__)

def process(...) -> Optional[DisplayBlock]:
    try:
        # ... processing logic ...
        if some_condition:
            logger.debug("Condition met, processing message")
            # ... continue processing ...
        return display_block
    except Exception:
        logger.warning("Error during processing, returning None")
        return None
```

---

## Code Review Checklist

When reviewing code, ensure:

1. **Core modules:**
   - No file I/O (except logging)
   - No network requests
   - No database access
   - No mutable global state
   - All inputs are treated as immutable
   - Functions are deterministic (same input → same output)

2. **Adapter modules:**
   - All core calls are wrapped in try/except
   - Errors from core are logged but not shown to users
   - Proper handling of platform-specific errors
   - Configuration validation is performed

3. **Testing:**
   - Core tests use frozen time
   - Core tests don't require network access
   - Tests are deterministic (no randomness)

---

## Common Pitfalls

### ❌ Don't do this:

```python
# In core module
def process(...):
    with open('config.json', 'r') as f:  # ❌ File I/O
        config = json.load(f)
    
    global_counter += 1  # ❌ Mutable global state
    
    result = requests.get('https://api.example.com')  # ❌ Network request
```

### ✅ Do this instead:

```python
# In core module
def process(..., config: CoreConfig):  # ✅ Config passed as argument
    # ✅ No file I/O, no network, no global state
    logger.debug("Processing message")  # ✅ Logging is OK
    return result
```

---

## Frozen Decisions (SPEC_FREEZE v1.0.2)

After specification freeze, the following decisions are **locked** and must not be changed without explicit approval as v2:

### D-001: Compact UTC Offsets
- **Status:** CLOSED
- **Rule:** Compact offsets of form `+HHMM` (e.g., `+0300`) are **NOT supported**
- **Allowed formats:** `+HH`, `+HH:MM`, `UTC+H`, `GMT-HH:MM`
- **Test:** `test_compact_offset_rejected_d001` in `test_timezone_extractor.py`

### FIFO Eviction Semantics
- **Rule:** `reply_mapping` and `processed_message_ids` use strict FIFO eviction
- **Constraint:** Updating an existing key **MUST NOT** change its insertion order (no move-to-end)
- **Implementation:** `OrderedDict` with `popitem(last=False)` for eviction
- **Test:** `TestFIFOEviction` in `test_adapter_config.py`

### SOURCE_FIRST Ordering + UTC Display
- **Rule:** `+00:00` offset is displayed as `UTC` (not `+00:00`)
- **Test:** `test_utc_offset_normalized_to_iana` in `test_timezone_converter.py`

### Pre-Change Checklist

Before making any changes to parsing, resolution, or ordering logic:

1. **Check SPEC_FREEZE.md** — Is this behavior locked?
2. **Check Decision Log** — Is there a closed decision (D-XXX) about this?
3. **Run relevant tests** — Do existing tests cover this behavior?
4. **If in doubt, ask** — Behavior-changing modifications require v2 approval

---

## References

- `SPEC_FREEZE.md` — Frozen behavioral specification (v1.0.2 final)
- `ARCHITECTURAL_INVARIANTS.md` — System invariants (including logging exception)
- `IMPLEMENTATION_CONSTRAINTS.md` — Hard rules for implementation
- `CORE_CONTRACT.md` — Core invocation interface

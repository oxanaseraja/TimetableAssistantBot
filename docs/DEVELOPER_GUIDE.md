# Developer Guide — Practical Guidelines for Team

This document provides practical guidelines for developers working on the TimetableAssistantBot project.

---

## Logging in Core Modules

### Policy

Core modules may use Python's standard `logging` module for debug/info/warning messages. This does not affect function purity or deterministic behavior.

### Guidelines

1. **Purpose:** Logging in core modules should remain only for monitoring and debugging purposes, without changing function state.

2. **What to log:**
   - Debug messages for troubleshooting (e.g., "Message discarded: exceeds max_time_mentions limit")
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

## References

- `ARCHITECTURAL_INVARIANTS.md` — System invariants (including logging exception)
- `IMPLEMENTATION_CONSTRAINTS.md` — Hard rules for implementation
- `CORE_CONTRACT.md` — Core invocation interface

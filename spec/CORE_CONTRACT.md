# CORE_CONTRACT.md — Core Invocation Interface (MVP)

This document defines how adapters invoke the core.

---

## CoreProcessor Interface

```python
def process(
    event: CoreMessageEvent,
    user_profile: UserProfile,
    channel_context: ChannelContext
) -> DisplayBlock | None
```

**Arguments:**
- `event` — the message to process
- `user_profile` — timezone info for message author (may have null timezone)
- `channel_context` — channel default and active timezones

**Returns:**
- `DisplayBlock` — formatted output for adapter to render
- `None` — no output (no time detected, ambiguity, suppression)

---

## Rules

1. **Synchronous call** — no async, no callbacks
2. **Pure function** — no side effects, no I/O, no storage access
3. **Deterministic** — same inputs always produce same output
4. **Never raises exceptions** — all errors result in `None`

---

## Data Flow

```
Adapter constructs:
  - CoreMessageEvent (from platform event)
  - UserProfile (from users.json lookup)
  - ChannelContext (from users.json lookup)

Adapter calls:
  result = process(event, user_profile, channel_context)

Adapter handles result:
  - if result is None → send nothing
  - if result is DisplayBlock → format and send
```

---

## Critical Constraints

- **Core does not know where data comes from**
- **Core has no access to storage or files**
- **Core is deterministic from these three arguments only**
- **Adapter is responsible for constructing all inputs**

This ensures core is testable in complete isolation.

---

## Adapter Obligations

- If `None`, send nothing
- Adapter never formats without a `DisplayBlock`
- Adapter must catch any unexpected exceptions (defensive)

---

## References

- `CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — how adapter constructs UserProfile
- `ARCHITECTURAL_INVARIANTS.md` — purity constraints

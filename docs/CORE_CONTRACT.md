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

## References

- `CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — how adapter constructs UserProfile
- `ARCHITECTURAL_INVARIANTS.md` — purity constraints

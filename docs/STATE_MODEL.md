# STATE_MODEL.md — MVP State Ownership

This document defines minimal state ownership for MVP.

---

## Core State

Core does not own storage in MVP.
It receives:
- `UserProfile`
- `ChannelContext`

Core treats them as inputs only.

ActiveTimezoneSet is derived from `ChannelContext` without activity tracking.
Decay/activity-based updates are out of scope for MVP.

---

## Adapter State

RuntimeState (MVP) — see `ADAPTER_CONTRACTS.md` §4 for full definition and rules:
- `processed_message_ids`: in-memory, FIFO-ordered (OrderedDict or equivalent); prevents duplicate processing
- `reply_mapping`: in-memory, FIFO-ordered (OrderedDict or equivalent); maps original message → bot reply ID (edit/delete handling)
- `id_mapping`: optional persistence (path from config, e.g. `persistence_path`); platform-specific; see `TELEGRAM_ADAPTER.md`

Adapter also loads at startup (not part of RuntimeState):
- `city_index` from `cities.json` (path from config); passed to core as argument

Persistence (id_mapping only, if path configured):
- Load on startup if file exists
- Save on graceful shutdown
- Failures ignored

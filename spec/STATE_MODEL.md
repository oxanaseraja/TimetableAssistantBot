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

RuntimeState (MVP):
- `processed_message_ids`: in-memory set
- `id_mapping`: optional persistence via `adapter_mapping.json`
- `city_list`: local file (`cities.json`) loaded by adapter

Persistence:
- Optional / Future
- Load on startup if file exists
- Save on graceful shutdown
- Failures ignored

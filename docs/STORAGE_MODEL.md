# STORAGE_MODEL.md — MVP vs Production Storage

This document describes what is stored locally in MVP and how storage is expected
to evolve in production.

---

## MVP (Local Only)

**Adapter runtime (in-memory):**
- `processed_message_ids` — prevents duplicate processing (process lifetime only).
- `reply_mapping` — original message → bot reply ID (edit/delete handling); process lifetime only.

**Adapter local files (paths from config):**
- City list — path from config (e.g. `data.cities_path`); used for extraction and output grouping.
- ID mapping — optional; path from config (e.g. `telegram.persistence_path`); example filename `adapter_mapping.json` (see `ADAPTER_CONTRACTS.md` §4, `TELEGRAM_ADAPTER.md`).

**Configuration:**
- `configuration.yaml` — static config (token, chat_id, limits).

**Core:**
- No storage in MVP.
- Core receives `UserProfile` and `ChannelContext` as inputs only.

---

## Production (Expected)

**Persistent storage (DB/KV):**
- User profiles (`UserProfile.timezone`)
- Channel context (`ChannelContext`, active timezones)
- Adapter message mappings (message → reply)

**Datasets:**
- Managed city list (versioned, updateable)
- IANA timezone data updates

**Operational storage:**
- Logs and metrics storage
- Error traces for debugging

---

## Notes

- MVP storage is intentionally minimal to keep the architecture deterministic.
- Production storage choices are out of scope for MVP and should be selected
  based on deployment constraints.

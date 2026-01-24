# TELEGRAM_ADAPTER.md — MVP Integration Plan

**Purpose:** Connect platform-agnostic core (`ARCHMINI.md`) to Telegram.  
**Scope:** MVP only. Discord/WhatsApp — Optional / Future.

Authoritative references:
- `POLICIES.md` — deterministic rules (including adapter rules)
- `CONTRACTS.md` — DTO contracts
- `ADAPTER_CONTRACTS.md` — adapter runtime contract

---

## 1. Responsibilities (Adapter Only)

1. **Platform Event Handling**
   - Subscribe to messages in a single Telegram chat (MVP).
   - Handle **new messages** and **edits only**.
   - Delete events are ignored (MVP rule).

2. **ID Mapping**
   - Deterministic SHA256 mapping (see `POLICIES.md`).
   - Core never receives platform identifiers.

3. **Core Invocation**
   - Convert Telegram update → `CoreMessageEvent`.
   - Pass DTO to core pipeline.
   - If core returns `None`, send nothing.

4. **Output Handling**
   - Receive `DisplayBlock` from core.
   - Render one line per timezone.
   - Cap to 5 lines.
   - Ignore `cities` in MVP (`cities = []`).

5. **Duplicate Suppression**
   - Deterministic rule by `internal_message_id` (see `POLICIES.md`).
   - In-memory only; optional persistence only hydrates this set at startup.

6. **Persistence (Optional / Future)**
   - `adapter_mapping.json` load/save on startup/shutdown (see `POLICIES.md`).
   - Failures are ignored (adapter continues with empty mapping).

---

## 2. Minimal File Structure

```
adapters/telegram/
├─ adapter.py           # bridge to Telegram API
├─ event_mapping.py     # Telegram update → CoreMessageEvent
├─ dispatcher.py        # DisplayBlock → Telegram message
├─ README.md            # adapter overview
```

---

## 3. Core DTO Mapping

```
CoreMessageEvent {
    internal_message_id,
    internal_user_id,
    internal_channel_id,
    text,
    is_edit,
    timestamp_utc
}
```

All internal IDs are derived from platform IDs using SHA256 (see `POLICIES.md`).

Deterministic mapping (Telegram):
```
internal_message_id = SHA256(f"{telegram_chat_id}:{telegram_message_id}")
internal_user_id = SHA256(f"telegram:{telegram_user_id}")
internal_channel_id = SHA256(f"telegram:{telegram_chat_id}")
```

---

## 4. Output Rendering (MVP)

For each `DisplayBlock.entries` item:

```
HH:MM <timezone> (City1, City2)
```

Rules:
- One line per timezone.
- Max 5 lines.
- Cities loaded from local list, grouped by timezone, sorted alphabetically.
- If cities list is empty → omit parentheses.
- Output format follows `ADAPTER_CONTRACTS.md`.

Edit handling:
- Always delete the old reply.
- Send a fully recomputed reply (up to 5 lines).

---

## 5. Adapter Configuration (MVP)

Defined in root `configuration.yaml`:

```yaml
telegram:
  token: "<TOKEN>"
  chat_id: "<MVP_CHAT_ID>"
  max_lines: 5
  persistence_path: "adapter_mapping.json"
  retry_attempts: 3
  cities_path: "cities.json"
```

---

## 6. Non-Goals (MVP)

- Delete events handling
- Message threading
- Persistence beyond optional `adapter_mapping.json`
- Multi-chat / multi-platform routing

---

## 7. Runtime Model (MVP)

- Long polling
- Single process
- Stateless except in-memory runtime state

See: `ADAPTER_CONTRACTS.md` for platform constraints and error handling.
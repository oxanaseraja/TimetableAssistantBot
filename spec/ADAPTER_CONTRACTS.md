# ADAPTER_CONTRACTS.md — Adapter Runtime Contract (MVP)

This document defines adapter behavior that is common to all platforms.
It is independent of any specific platform implementation.

---

## 1. Core Invocation Contract

Interface:

```python
def process(
    event: CoreMessageEvent,
    user_profile: UserProfile,
    channel_context: ChannelContext,
    city_index: Mapping[str, str],
    config: CoreConfig
) -> DisplayBlock | None
```

See `CORE_CONTRACT.md` for full specification.

Rules:
- Call is synchronous.
- Core must not raise exceptions to the adapter.
- If core returns `None`, adapter sends nothing.
- `city_index` and `config` are loaded once at startup, reused for all messages.

---

## 2. Error Handling Policy (Adapter Level)

Telegram API errors:
- Network / 5xx → retry_attempts total (including first attempt), fixed backoff 500ms.
- 4xx (invalid token, forbidden) → log and disable adapter.
- Send failure after retries → log only, no further retries.

Core errors:
- Any core error is logged.
- User receives no error message in MVP.
- Adapter continues running.

---

## 2.1 Security (MVP)

- Token is supplied via config/env only.
- Token is never stored in repo.
- No rotation in MVP.
- Missing/invalid token → fail fast, no retries.

---

## 2.2 Observability (MVP)

- Structured logs only.
- Error counters are recorded.
- No alerts in MVP.

---

## 3. Lifecycle Scope (Platform Constraints)

Supported events (MVP):
- NEW_MESSAGE
- EDIT_MESSAGE

Unsupported (MVP):
- DELETE_MESSAGE
- THREAD_EVENTS
- REACTIONS

Rule:
If adapter receives unsupported event → ignore silently.

---

## 4. Adapter Runtime State Model

```
RuntimeState {
    processed_message_ids: Set<string>,                    // in-memory
    reply_mapping: Dict<internal_message_id, platform_reply_id>,  // in-memory
    id_mapping: Dict<platform_id, internal_id>             // optional, persisted
}
```

Rules:

**processed_message_ids:**
- in-memory only
- TTL = process lifetime
- cleared on restart
- max size = 10_000, drop oldest FIFO

**reply_mapping:**
- in-memory only
- maps original message → bot's reply message ID
- used for edit/delete handling
- max size = 10_000, drop oldest FIFO

**id_mapping:**
- optional persistence
- load on startup if file exists
- save on graceful shutdown
- failure to load/save → ignored

---

### Edit Handling Algorithm

```
on_edit(message):
    internal_id = hash(message)
    
    # 1. Delete previous reply if exists
    if internal_id in reply_mapping:
        old_reply_id = reply_mapping[internal_id]
        try:
            delete_message(old_reply_id)
        except:
            pass  # ignore errors
    
    # 2. Reprocess message
    result = core.process(message)
    
    # 3. Send new reply and update mapping
    if result:
        new_reply = send_message(format(result))
        reply_mapping[internal_id] = new_reply.id
    else:
        reply_mapping.pop(internal_id, None)
```

---

## 5. Config Contract

```yaml
telegram:
  token: string              # required (or from env)
  chat_id: string            # required
  max_lines: int = 5         # optional, default 5
  persistence_path: string | null = null
  retry_attempts: int = 3

data:
  cities_path: string        # required (path to cities.json)
  users_path: string         # required (path to users.json)

core:
  max_time_mentions: int = 3
  max_timezones: int = 5
  ordering: string = "SOURCE_FIRST"
  default_timezone: string | null = null
```

**Structure notes:**
- `data:` section contains paths to data files (platform-agnostic)
- `core:` section maps to `CoreConfig` DTO
- This structure scales better for multi-platform support

Rules:
- Missing required → adapter does not start.
- Defaults applied deterministically.
- No dynamic reload in MVP.

---

## 6. Output Formatting Contract

Rules:
- Always 24-hour format.
- Zero-padded HH:MM.
- Timezone shown as IANA id.
 - Cities shown in parentheses if present, alphabetical order.
 - If cities list is empty → omit parentheses.

Format:

```
{HH:MM} {timezone_id} (City1, City2)
```

Example:

```
10:30 Europe/Amsterdam
11:30 Europe/Nicosia
```

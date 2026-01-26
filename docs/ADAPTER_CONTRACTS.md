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

## 2.3 Message Timestamp Requirement

**Requirement:** All platform messages must have a valid timestamp.

**Behavior if timestamp is missing:**
- Adapter must discard the event
- Core is not called
- No reply is sent
- Event may be logged as invalid (optional)

**Rationale:**
- Core requires deterministic timestamp for DST calculations
- Using system clock (`datetime.now()`) violates Core Invariant #1 (no system clock)
- Ensures reproducible behavior and testability
- This behavior takes precedence over any other specification that might suggest using current time

**Note:** This requirement ensures that core processing is deterministic and testable. Any platform adapter implementation must reject messages without timestamps rather than substituting system time.

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
    processed_message_ids: OrderedDict<string, None>,       // in-memory, FIFO-ordered
    reply_mapping: OrderedDict<internal_message_id, platform_reply_id>,  // in-memory, FIFO-ordered
    id_mapping: Dict<platform_id, internal_id>             // optional, persisted
}
```

Rules:

**processed_message_ids:**
- in-memory only
- TTL = process lifetime
- cleared on restart
- max size = 10_000, drop oldest FIFO
- **MUST be implemented using an insertion-ordered structure (`OrderedDict` or equivalent) to guarantee FIFO eviction independently of language implementation details**

**reply_mapping:**
- in-memory only
- maps original message → bot's reply message ID
- used for edit/delete handling
- max size = 10_000, drop oldest FIFO
- **MUST be implemented using an insertion-ordered structure (`OrderedDict` or equivalent) to guarantee FIFO eviction independently of language implementation details**

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

**Cleanup Error Handling:**
- Errors during cleanup operations (delete old reply) must not affect message processing
- Errors may be logged (implementation detail)
- Processing continues regardless of cleanup success/failure

---

## 5. Config Contract

```yaml
telegram:
  token: string              # required (or from env TELEGRAM_TOKEN)
  chat_id: string            # required, numeric string (converted to int by adapter)
  persistence_path: string | null = null
  retry_attempts: int = 3

data:
  cities_path: string        # required (path to cities.json)
  users_path: string         # required (path to users.json)

**Empty cities.json behavior:**

An empty `cities.json` (`[]`) is a **valid state**.

In this case:
- City name extraction will not find any matches
- System relies on IANA timezone IDs and offset strings only
- No cities will be displayed in output (empty cities list)
- Adapter starts normally with empty city index

System behavior:
- Extraction still works for offsets and IANA IDs
- Resolution falls back to user/channel/system defaults
- This is a valid system state and does not cause errors
- Adapter may log info message: "Loaded empty cities.json, city extraction disabled"

core:
  max_time_mentions: int = 3 # max times to parse per message

output:
  max_timezones: int = 5     # max timezones in DisplayBlock
  max_lines: int = 5         # max lines in adapter output
  ordering: string = "SOURCE_FIRST"
```

**Structure notes:**
- `telegram:` — platform-specific settings
- `data:` — paths to data files (platform-agnostic)
- `core:` — core processing settings (maps to CoreConfig.max_time_mentions)
- `output:` — output formatting settings (maps to CoreConfig.max_timezones, ordering)

**Rationale for core/output split:**
- `core:` = things that affect parsing/processing
- `output:` = things that affect display/formatting
- Clearer separation of concerns

Rules:
- Missing required → adapter does not start.
- Defaults applied deterministically.
- No dynamic reload in MVP.

**Empty or Invalid Configuration:**
- If configuration file is empty or contains only comments → treat as empty config dictionary `{}`
- All values use defaults as specified in `CONTRACTS.md`
- Adapter starts normally with default configuration
- If YAML syntax is invalid → `yaml.YAMLError` is raised → adapter does not start

**Configuration Validation Rules:**

All configuration values must be validated according to these rules:

**Type Validation:**
- `max_time_mentions`: Must be integer. If string, attempt conversion. If conversion fails → use default 3, log warning.
- `max_timezones`: Must be integer. If string, attempt conversion. If conversion fails → use default 5, log warning.
- `ordering`: Must be string. If not string → use default "SOURCE_FIRST", log warning.
- `default_timezone`: Must be string or null. If not → treat as null (UTC), log warning.
- `max_lines`: Must be integer. If string, attempt conversion. If conversion fails → use default 5, log warning.
- `retry_attempts`: Must be integer. If string, attempt conversion. If conversion fails → use default 3, log warning.

**Range Validation:**
- `max_time_mentions`: Must be integer in range [1, 100]. Invalid values → use default 3, log warning.
- `max_timezones`: Must be integer in range [1, 100]. Invalid values → use default 5, log warning.
- `ordering`: Must be one of "SOURCE_FIRST", "OFFSET_ASC", "ALPHABETICAL". Invalid values → use default "SOURCE_FIRST", log warning.
- `default_timezone`: Must be valid IANA timezone ID or null. Invalid values → treat as null (UTC), log warning.
- `max_lines`: Must be integer in range [1, 100]. Invalid values → use default 5, log warning.
- `retry_attempts`: Must be integer in range [1, 10]. Invalid values → use default 3, log warning.

**Behavior:**
- All validation errors are logged as warnings
- Adapter continues with defaults for invalid values
- No partial startup: adapter starts normally with validated/default values

**Error Handling:**
- If `zoneinfo.available_timezones()` raises exception during validation → treat as invalid, use default, log warning
- If timezone validation fails due to system errors (TypeError, AttributeError, etc.) → treat as invalid, use default, log warning
- Adapter continues with default value
- System errors during validation do not prevent adapter startup

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

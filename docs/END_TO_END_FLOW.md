# END_TO_END_FLOW.md — End-to-End Walkthrough (MVP)

This is a deterministic, step-by-step walkthrough for a single message.
It shows all DTOs, transformations, and stop/suppression points.

---

## Example Input (single message)

Telegram message:
- text: `"See you at 10:30 Amsterdam"`
- telegram_user_id: `123`
- telegram_chat_id: `-1001`
- telegram_message_id: `555`
- is_edit: `false`
- timestamp_utc: `2026-01-25T12:00:00Z`

---

## Step 0 — Adapter Event Mapping

**Input:** Telegram update  
**Output DTO:** `CoreMessageEvent`

```
CoreMessageEvent {
  internal_message_id: SHA256("-1001:555"),
  internal_user_id: SHA256("telegram:123"),
  internal_channel_id: SHA256("telegram:-1001"),
  text: "See you at 10:30 Amsterdam",
  is_edit: false,
  timestamp_utc: "2026-01-25T12:00:00Z"
}
```

---

## Step 1 — Time Detection (Regex-based)

**Input:** `CoreMessageEvent.text`  
**Output DTO:** `DetectedTime[]`  
**Method:** Regex patterns only (see `POLICIES.md` §1.1). No LLM interpretation.

```
DetectedTime [
  {
    raw_text: "10:30",
    hour: 10,
    minute: 30,
    am_pm: null,
    position_start: 11,
    position_end: 16,
    ambiguous: false
  }
]
```

**Stop condition:** if empty → return `None`.

---

## Step 2 — Timezone Signals

**Input:** message + context  
**Output DTO:** `TimezoneSignals`

```
TimezoneSignals {
  explicit_timezone: "Europe/Amsterdam",
  user_timezone: "Europe/Amsterdam",
  channel_timezone: null,
  active_timezones: ["Europe/Amsterdam", "Asia/Yerevan"]
}
```

---

## Step 3 — Resolution

**Input:** `DetectedTime` + `TimezoneSignals`  
**Output DTO:** `ResolvedTimeContext`

```
ResolvedTimeContext {
  base_timezone: "Europe/Amsterdam",
  ambiguity: "NONE",
  resolution_source: "EXPLICIT_HINT",
  reason: "explicit hint in text"
}
```

**Suppression rule:** if ambiguity is `HIGH` → return `None`.

---

## Step 4 — Conversion

**Input:** base datetime + target timezones  
**Output DTO:** `ConvertedTime[]`

```
ConvertedTime [
  {
    timezone_id: "Europe/Amsterdam",
    local_time: "2026-01-25T10:30:00+01:00",
    utc_offset: "+01:00"
  },
  {
    timezone_id: "Asia/Yerevan",
    local_time: "2026-01-25T13:30:00+04:00",
    utc_offset: "+04:00"
  }
]
```

---

## Step 5 — Output Assembly (Core)

**Input:** `ConvertedTime[]`  
**Output DTO:** `DisplayBlock`

```
DisplayBlock {
  entries: [
    {
      timezone: "Europe/Amsterdam",
      local_time: "10:30",
      cities: []
    },
    {
      timezone: "Asia/Yerevan",
      local_time: "13:30",
      cities: []
    }
  ],
  ordering: "SOURCE_FIRST",
  flags: { ambiguous: false, partial: false }
}
```

Core always returns `cities: []`; adapter populates cities from `cities.json` during formatting (Step 6).

---

## Step 6 — Adapter Output (Telegram)

**Input:** `DisplayBlock`  
**Output:** Telegram text reply (adapter fills cities from `cities.json` when formatting)

```
10:30 Europe/Amsterdam (Amsterdam)
13:30 Asia/Yerevan (Yerevan)
```

**Suppression:** if core returned `None` → adapter sends nothing.

---

## Alternative Stop Example (Ambiguous)

Message: `"See you at 8"`

- Time detected: `hour=8, minute=null, am_pm=null, ambiguous=true`
- Ambiguity policy → core returns `None`
- Adapter sends no reply

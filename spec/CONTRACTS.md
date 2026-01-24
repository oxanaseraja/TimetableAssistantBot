# CONTRACTS.md — Core DTO Pack (MVP)

Contracts are deterministic and platform-agnostic.
Core never receives platform identifiers.
MVP platform: Telegram.

---

## CoreMessageEvent

```
CoreMessageEvent {
    internal_message_id: string,
    internal_user_id: string,
    internal_channel_id: string,
    text: string,
    is_edit: boolean,
    timestamp_utc: datetime
}
```

---

## DetectedTime

```
DetectedTime {
    raw_text: string,
    hour: int,
    minute?: int,
    am_pm?: "AM" | "PM",
    position_start: int,
    position_end: int,
    ambiguous: boolean
}
```

---

## TimezoneSignals

```
TimezoneSignals {
    explicit_timezone?: string,   // IANA id or offset
    user_timezone?: string,
    channel_timezone?: string,
    active_timezones: List<string>
}
```

---

## ResolvedTimeContext

```
ResolvedTimeContext {
    base_timezone?: string,
    ambiguity: "NONE" | "HIGH",
    resolution_source?: "EXPLICIT_HINT" | "USER_PROFILE" | "CHANNEL_DEFAULT" | "ACTIVE_TZ_SINGLE",
    reason?: string
}
```

---

## ConvertedTime

```
ConvertedTime {
    timezone_id: string,
    local_time: datetime,
    utc_offset: string
}
```

---

## DisplayBlock

```
DisplayBlock {
    entries: List<{
        timezone: string,
        local_time: string,
        cities: List<string> // populated from local city list in adapter
    }>,
    ordering: string,
    flags: {
        ambiguous: boolean,
        partial: boolean
    }
}
```

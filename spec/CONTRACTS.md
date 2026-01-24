# CONTRACTS.md — Core DTO Pack (MVP)

Contracts are deterministic and platform-agnostic.
Core never receives platform identifiers.
MVP platform: Telegram.

---

## CoreMessageEvent

```
CoreMessageEvent {
    internal_message_id: string,   // SHA256 hash, hex encoded
    internal_user_id: string,      // SHA256 hash, hex encoded
    internal_channel_id: string,   // SHA256 hash, hex encoded
    text: string,                  // original message text
    is_edit: boolean,              // true if this is an edit event
    timestamp_utc: datetime        // timezone-aware, UTC (used for DST)
}
```

**Note:** `timestamp_utc` must be a timezone-aware datetime object in UTC.
Used as reference date for DST calculations.

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
        timezone: string,       // IANA timezone ID
        local_time: string,     // HH:MM format (24-hour, zero-padded)
        cities: List<string>    // populated by adapter from cities.json
    }>,
    ordering: Ordering,
    flags: DisplayFlags
}

Ordering = "SOURCE_FIRST" | "OFFSET_ASC"
// SOURCE_FIRST: source timezone first, then channel default, then by offset
// OFFSET_ASC: sorted by UTC offset ascending, then alphabetically

DisplayFlags {
    ambiguous: boolean,   // true if any input time was ambiguous
    partial: boolean      // true if some timezones were omitted due to max limit (5)
}
```

**Notes:**
- `partial = true` only when `len(active_timezones) > max_display_limit`
- `ambiguous` is informational; if truly ambiguous, core returns None instead
- Adapter uses `ordering` to verify output order matches expectation

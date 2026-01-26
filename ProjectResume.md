5 блоков:

1. Общая философия и цель контрактов
2. Инварианты системы (что никогда не должно нарушаться)
3. Контракты между слоями (core / adapter / storage)
4. Поток данных: вход → преобразования → выход
5. Failure modes и гарантии

---

# Architectural Invariants & Contracts

*(Core system behavior and interface guarantees)*

## 1. Purpose of this section

This section defines **architectural invariants and interface contracts** of the Timetable Assistant Bot.

Its goals:

* Fix product-critical behavior
* Eliminate ambiguous interpretations between components
* Make the system deterministic and testable
* Preserve implementation freedom where it does not affect observable behavior

This section intentionally does **not** describe:

* specific libraries
* concrete algorithms
* data structures in a specific language
* logging, imports, or runtime details

Only **behavioral contracts** and **cross-layer invariants** are defined.

---

## 2. Global System Invariants

These rules must hold in **all valid executions** of the system.

### 2.1. Safety-first invariant

> The system must never produce a reply if the interpretation of time or timezone is ambiguous.

This includes:

* ambiguous hour without AM/PM
* unresolved timezone
* conflicting timezone signals
* multiple possible interpretations

**Result:**
If ambiguity exists → the system produces **no output**.

---

### 2.2. Determinism invariant

Given:

* the same message text
* the same user profile state
* the same channel state
* the same message timestamp

The system must always produce:

* the same resolved timezone
* the same converted times
* the same output ordering

No randomness, no context leakage, no heuristic instability.

---

### 2.3. Layer isolation invariant

* Core must not depend on platform APIs
* Core must not know about Telegram / Discord
* Adapter must not implement business logic
* Converter must be the only place where timezone validity is enforced

---

## 3. Data Domain Contracts

### 3.1. Allowed timezone formats by domain

This is a **strict contract**.

| Domain                         | Allowed formats               |
| ------------------------------ | ----------------------------- |
| users.json (user timezone)     | IANA timezone IDs only        |
| users.json (channel default)   | IANA timezone IDs only        |
| active_timezones               | IANA timezone IDs only        |
| Explicit hints in message text | IANA IDs or offset strings    |
| Internal resolved timezone     | IANA ID or offset (temporary) |

#### Rationale

* Profiles represent **stable identity state**
* Offset strings:

  * do not encode DST
  * are not stable across dates
  * cannot be validated via zoneinfo
* Offsets are only valid as **situational hints**

---

### 3.2. Users and channels storage invariants

#### users.json validity

`users.json` may be:

* missing
* empty (`{}`)
* partially filled

All of these are **valid system states**.

#### Behavior with empty users.json

If users.json is empty:

* all users have `timezone = None`
* all channels have `default_timezone = None`
* active_timezones may be empty

Resolution behavior:

* explicit hints are still used
* otherwise SYSTEM_DEFAULT may be used
* if no timezone can be resolved → no reply

The system must:

* start normally
* not crash
* not require profiles to exist

---

## 4. Layer Contracts

---

## 4.1. Adapter → Core Contract

### Input event guarantees

Adapter must provide to core:

```
CoreMessageEvent:
- internal_message_id   (string, stable)
- internal_user_id      (string, stable)
- internal_channel_id   (string, stable)
- text                  (string, raw message text)
- timestamp_utc         (datetime, timezone-aware UTC)
- is_edit               (bool)
```

### Adapter responsibilities

Adapter is responsible for:

* receiving platform events
* mapping platform IDs to internal IDs
* attaching timestamp
* loading user/channel context
* calling core exactly once per event

Adapter must **not**:

* parse time
* parse timezone
* resolve ambiguity
* perform conversion

---

## 4.2. Core Processing Contract

Core processes each message as a **pure function**:

```
(CoreMessageEvent, UserContext, ChannelContext) 
        → DisplayBlock | None
```

### Core guarantees

Core must:

* never mutate adapter state
* never call platform APIs
* never store persistent data
* return either:

  * DisplayBlock
  * None

Returning None means:

* no time found
* ambiguous interpretation
* unresolved timezone
* safety stop

---

## 4.3. Extractor Contract

### Time extraction

* Core scans text using deterministic patterns
* At most **N = 3** time mentions are detected
* For MVP, **only the first detected time is processed**

#### Invariant

> The extractor must never process more than one time per message in MVP.

Additional detected times are:

* parsed (for ambiguity detection)
* but ignored for output

---

### Timezone signal extraction

Signals may be extracted from:

1. explicit UTC/GMT offsets
2. explicit IANA IDs
3. city names from whitelist

Priority order is fixed.

#### Multiple matches of same priority

If multiple signals of the same priority exist:

1. select the signal closest to the time mention
2. if distance equal → select first in text order

This guarantees determinism.

---

## 4.4. Resolver Contract

Resolver receives:

```
signals:
- explicit_timezone   (string | None)
- user_timezone       (IANA | None)
- channel_timezone    (IANA | None)
- active_timezones    (List[IANA])
```

### Resolver responsibilities

Resolver must:

* select the timezone source according to priority rules
* return either:

  * resolved_timezone (string)
  * None

Resolver must **not**:

* validate timezone format
* distinguish offset vs IANA
* perform conversion

Resolver treats timezone strings as **opaque identifiers**.

All format validation is deferred to the converter.

---

## 4.5. Converter Contract

Converter is the **only component** allowed to:

* validate timezone identifiers
* interpret offset strings
* interact with zoneinfo
* handle DST

### Converter behavior

For each target timezone:

* invalid timezone → skipped
* conversion error → skipped
* valid timezone → included

Converter must never:

* raise on individual timezone failure
* abort entire conversion because of one invalid entry

---

## 5. Output Contract (DisplayBlock)

### 5.1. DisplayBlock structure

Core returns:

```
DisplayBlock:
- entries: List[Entry]
- ordering: string
- flags:
    - ambiguous: bool
    - partial: bool
```

### 5.2. Entry format (strict)

Each entry must have exactly:

```json
{
  "timezone": "string",      // IANA ID or offset string
  "local_time": "HH:MM",     // 24-hour, zero-padded
  "cities": ["string"]      // may be empty
}
```

#### Formatting invariants

* `local_time` is always `HH:MM` (24-hour)
* zero-padded
* no seconds
* no AM/PM

---

### 5.3. Ordering invariants

Entries must be ordered as:

1. source timezone (where original time was expressed)
2. channel default timezone (if different)
3. remaining active timezones ordered by:

   * UTC offset ascending
   * then alphabetically by timezone ID

Ordering must be deterministic.

---

## 6. Adapter Output Contract

Adapter receives DisplayBlock and is responsible for:

* mapping timezones to cities
* formatting human-readable strings
* posting reply as a threaded / reply message
* tracking reply message ID for edits

Adapter must not:

* reorder entries
* change times
* filter entries

---

## 7. Failure Modes & Guarantees

---

### 7.1. Message without timestamp

If timestamp is missing:

* adapter must discard the event
* core is not called
* no reply is sent
* event may be logged as invalid (optional)

**Rationale:**
* Core requires deterministic timestamp for DST calculations
* Using system clock (`datetime.now()`) violates Core Invariant #1 (no system clock)
* Ensures reproducible behavior and testability

**Note:** This requirement ensures that core processing is deterministic and testable. Any platform adapter implementation must reject messages without timestamps rather than substituting system time.

---

### 7.2. Message edit handling

If message is edited:

* previous bot reply (if exists) is deleted
* message is reprocessed from scratch
* new reply is posted or not posted

---

### 7.3. Partial conversion

If some target timezones fail conversion:

* valid ones are still returned
* `flags.partial = true`
* adapter may optionally annotate partial output

System must never:

* fail entire reply because of one timezone
* throw visible errors to user

---

## 7.4. Hard stop conditions

Core must return None (no output) if:

* no time found
* timezone cannot be resolved
* ambiguity detected
* resolved timezone invalid
* zero valid target timezones remain

---

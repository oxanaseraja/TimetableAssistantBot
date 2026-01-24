# TIMEZONE_EXTRACTION_RULES.md — MVP Rules

This document defines how timezone hints are extracted from message text.
All matching is **deterministic** — regex and exact lookup only.

---

## 1. Supported Timezone Signals (Priority Order)

Signals are checked in this order. First match wins.

### 1.1 Explicit UTC/GMT Offset

**Pattern:** `(UTC|GMT)?[+-]\d{1,2}(:\d{2})?`

**Examples:**
| Input | Parsed Offset |
|-------|---------------|
| `UTC+2` | `+02:00` |
| `GMT-5` | `-05:00` |
| `+0300` | `+03:00` |
| `+3` | `+03:00` |
| `-05:30` | `-05:30` |

**Rules:**
- Case-insensitive (`utc`, `UTC`, `Utc` all valid)
- Normalize to `±HH:MM` format internally

---

### 1.2 Explicit IANA Timezone ID

**Pattern:** `[A-Za-z_]+/[A-Za-z_]+`

**Examples:**
- `Europe/Amsterdam`
- `Asia/Yerevan`
- `America/New_York`

**Rules:**
- Must be valid IANA timezone (validate against `zoneinfo.available_timezones()`)
- Case-sensitive (IANA IDs are case-sensitive)
- Word boundary required

---

### 1.3 City Name (from cities.json)

**Lookup:** Exact match against `cities.json` whitelist.

**Rules:**
- Case-insensitive
- Whole token match only (word boundary)
- No substring matches

**Examples:**
| Input | Match? |
|-------|--------|
| `"in Amsterdam"` | ✅ Yes |
| `"amsterdam"` | ✅ Yes |
| `"AMSTERDAM"` | ✅ Yes |
| `"Amsterdamn"` | ❌ No (typo) |
| `"New Amsterdam"` | ❌ No (not in whitelist) |

---

## 2. cities.json Format

**Storage format:** Object-based (extensible)

```json
[
  {
    "city": "Amsterdam",
    "country": "NL",
    "timezone": "Europe/Amsterdam",
    "aliases": ["AMS"]
  },
  {
    "city": "New York",
    "country": "US",
    "timezone": "America/New_York",
    "aliases": ["NYC", "NY"]
  }
]
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `city` | string | yes | Primary city name |
| `country` | string | yes | ISO 3166-1 alpha-2 country code |
| `timezone` | string | yes | IANA timezone ID |
| `aliases` | string[] | yes | Alternative names (can be empty) |

**Rules:**
- Each city/alias appears in exactly one entry
- No duplicates across entries
- Adapter loads this file at startup

---

## 2.1 Runtime Index

At startup, adapter builds a lookup index for O(1) matching:

```python
city_index: Dict[str, str] = {}  # lowercase name → timezone

for entry in cities_json:
    city_index[entry["city"].lower()] = entry["timezone"]
    for alias in entry["aliases"]:
        city_index[alias.lower()] = entry["timezone"]
```

**Usage:**
```python
def lookup_city(text: str) -> Optional[str]:
    for word in tokenize(text):
        if word.lower() in city_index:
            return city_index[word.lower()]
    return None
```

---

## 3. Matching Algorithm

```
function extract_timezone_hint(text, position, window=30):
    context = text[position-window : position+window]
    
    # Priority 1: UTC/GMT offset
    if match = TZ_OFFSET_REGEX.search(context):
        return normalize_offset(match)
    
    # Priority 2: IANA timezone ID
    if match = TZ_IANA_REGEX.search(context):
        if match.group() in zoneinfo.available_timezones():
            return match.group()
    
    # Priority 3: City lookup
    for word in tokenize(context):
        for tz, cities in cities_json.items():
            if word.lower() in [c.lower() for c in cities]:
                return tz
    
    return None
```

---

## 4. Ambiguity Handling

**Multiple matches in context:**
- If multiple timezone signals found → use first by priority order
- If same priority, use closest to time mention

**Conflicting signals:**
- `"10:30 Amsterdam UTC+5"` → use `UTC+5` (higher priority)

---

## 5. Out of Scope (MVP)

These are explicitly **NOT supported**:

| Type | Examples | Reason |
|------|----------|--------|
| Country names | `Germany`, `France` | Ambiguous (multiple timezones) |
| State names | `California`, `Texas` | Ambiguous |
| Abbreviations | `EST`, `CET`, `PST` | Ambiguous (DST, multiple regions) |
| Partial matches | `York` for `New York` | Too risky |

---

## 6. References

- `POLICIES.md` §1.4 — Timezone Hint Extraction
- `POLICIES.md` §3 — Timezone Resolution Precedence
- `cities.json` — City whitelist (adapter-owned)

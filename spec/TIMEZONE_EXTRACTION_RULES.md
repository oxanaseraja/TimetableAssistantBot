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

### 3.1 Tokenization

```python
def tokenize(text: str) -> List[str]:
    """
    Split text into word tokens.
    Uses word boundaries, preserves Unicode letters.
    Lowercasing is done during comparison, not here.
    """
    return re.findall(r'\b\w+\b', text, re.UNICODE)
```

**Examples:**
- `"in Amsterdam"` → `["in", "Amsterdam"]`
- `"10:30 UTC+2"` → `["10", "30", "UTC", "2"]`
- `"see you в Москве"` → `["see", "you", "в", "Москве"]`

### 3.2 Offset Normalization

```python
def normalize_offset(raw: str) -> str:
    """
    Normalize timezone offset to ±HH:MM format.
    
    Input formats: +3, +03, +0300, +03:00, UTC+3, GMT-5
    Output format: +03:00, -05:00
    """
    # Remove UTC/GMT prefix
    raw = re.sub(r'^(UTC|GMT)', '', raw, flags=re.IGNORECASE)
    
    # Extract sign
    sign = '+' if raw[0] != '-' else '-'
    raw = raw.lstrip('+-')
    
    # Parse hours and minutes
    if ':' in raw:
        parts = raw.split(':')
        hours, minutes = int(parts[0]), int(parts[1])
    elif len(raw) >= 3:
        hours = int(raw[:2])
        minutes = int(raw[2:4]) if len(raw) >= 4 else 0
    else:
        hours = int(raw)
        minutes = 0
    
    return f"{sign}{hours:02d}:{minutes:02d}"
```

**Examples:**
- `"+3"` → `"+03:00"`
- `"UTC+2"` → `"+02:00"`
- `"+0300"` → `"+03:00"`
- `"GMT-5"` → `"-05:00"`
- `"-05:30"` → `"-05:30"`

### 3.3 Main Extraction Algorithm

```python
def extract_timezone_hint(text: str, time_position: int, window: int = 30) -> Optional[str]:
    """
    Extract timezone hint from context around time mention.
    
    Args:
        text: Full message text
        time_position: Character position of time mention
        window: Characters to look before/after (default 30)
    
    Returns:
        IANA timezone ID, normalized offset, or None
    """
    start = max(0, time_position - window)
    end = min(len(text), time_position + window)
    context = text[start:end]
    
    # Priority 1: UTC/GMT offset
    TZ_OFFSET_REGEX = re.compile(r'(UTC|GMT)?[+-]\d{1,2}(:\d{2})?', re.IGNORECASE)
    match = TZ_OFFSET_REGEX.search(context)
    if match:
        return normalize_offset(match.group())
    
    # Priority 2: IANA timezone ID
    TZ_IANA_REGEX = re.compile(r'\b[A-Za-z_]+/[A-Za-z_]+\b')
    match = TZ_IANA_REGEX.search(context)
    if match and match.group() in zoneinfo.available_timezones():
        return match.group()
    
    # Priority 3: City lookup (uses pre-built index)
    for word in tokenize(context):
        if word.lower() in city_index:
            return city_index[word.lower()]
    
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

## 4.1 Hint Scope

**Timezone hint applies only to the time mention within ±30 chars window.**

Each time mention has its own independent timezone resolution.

Example:
```
Message: "Meeting in Amsterdam at 10:30, but John in NYC joins at 9:30"

Time 1: "10:30" at position 25
  - Window: [...Amsterdam at 10:30, but Jo...]
  - Hint found: "Amsterdam" → Europe/Amsterdam

Time 2: "9:30" at position 55
  - Window: [...NYC joins at 9:30]
  - Hint found: "NYC" → America/New_York
```

If no hint found in window → fall back to user/channel timezone.

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

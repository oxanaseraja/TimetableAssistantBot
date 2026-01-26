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

**Examples:**

Example 1: Empty cities.json with explicit offset
```
Input: "Meeting at 10:30 UTC+3"
cities.json: []
Result: Explicit offset "+03:00" extracted, city extraction returns None
Output: Time converted to UTC+3, no cities displayed
```

Example 2: Empty cities.json with IANA timezone
```
Input: "Call at 14:00 Europe/Amsterdam"
cities.json: []
Result: IANA timezone "Europe/Amsterdam" extracted, city extraction returns None
Output: Time converted to Europe/Amsterdam, no cities displayed
```

Example 3: Empty cities.json with city name (no match)
```
Input: "Meeting at 10:30 in Amsterdam"
cities.json: []
Result: No city match found, city extraction returns None
Output: Falls back to user/channel/system default timezone, no cities displayed
```

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
def normalize_offset(raw: str) -> Optional[str]:
    """
    Normalize timezone offset to ±HH:MM format.
    
    Input formats: +3, +03, +0300, +03:00, UTC+3, GMT-5
    Output format: +03:00, -05:00
    
    Returns:
        Normalized offset string (±HH:MM) or None if format is invalid or out of range.
        Invalid offsets MUST NOT be converted into "+00:00" to preserve signal integrity.
    
    Offset Range Validation:
        - Hours: [0, 14] (UTC offsets typically ±12, but allow up to ±14 for edge cases)
        - Minutes: [0, 59]
        - Offsets outside range → return None (ignored, no explicit hint found)
    """
    # Remove UTC/GMT prefix
    raw = re.sub(r'^(UTC|GMT)', '', raw, flags=re.IGNORECASE)
    
    # Extract sign
    sign = '+' if raw[0] != '-' else '-'
    raw = raw.lstrip('+-')
    
    # Parse hours and minutes
    try:
        if ':' in raw:
            parts = raw.split(':')
            hours, minutes = int(parts[0]), int(parts[1])
        elif len(raw) >= 3:
            hours = int(raw[:2])
            minutes = int(raw[2:4]) if len(raw) >= 4 else 0
        else:
            hours = int(raw)
            minutes = 0
        
        # Validate range: hours [0, 14], minutes [0, 59]
        if not (0 <= hours <= 14) or not (0 <= minutes <= 59):
            return None  # Out of range - ignore invalid offset
        
        return f"{sign}{hours:02d}:{minutes:02d}"
    except (ValueError, IndexError):
        # Invalid offset format - return None to indicate no explicit hint found
        # This preserves signal integrity: invalid offsets are ignored, not converted to UTC
        return None
```

**Examples:**
- `"+3"` → `"+03:00"`
- `"UTC+2"` → `"+02:00"`
- `"+0300"` → `"+03:00"`
- `"GMT-5"` → `"-05:00"`
- `"-05:30"` → `"-05:30"`

### 3.3 Main Extraction Algorithm

```python
def extract_timezone_hint(
    text: str,
    time_position: int,
    city_index: Mapping[str, str],
    window: int = 30
) -> Optional[str]:
    """
    Extract timezone hint from context around time mention.
    
    Args:
        text: Full message text
        time_position: Character position of time mention
        city_index: Pre-built city→timezone lookup (passed from adapter)
        window: Characters to look before/after (default 30)
    
    Returns:
        IANA timezone ID, normalized offset, or None
    
    Note: city_index is passed explicitly to maintain core purity (Invariant #7).
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
    
    # Priority 3: City lookup (uses passed index)
    for word in tokenize(context):
        if word.lower() in city_index:
            return city_index[word.lower()]
    
    return None
```

---

## 4. Ambiguity Handling

**Multiple matches in context:**

Deterministic selection algorithm:

1. **Priority order:** Signals are checked in priority order (§1):
   - Priority 1: UTC/GMT offset
   - Priority 2: IANA timezone ID
   - Priority 3: City name
   
   If multiple signals of **different priorities** are found → use highest priority signal.

2. **Same priority, multiple matches:**
   If multiple matches of the **same priority** are found:
   - Select the match **closest** to the time mention position (`time_position`)
   - Distance is calculated as absolute difference: `abs(match_position - time_position)`
   - **If distances are equal → select the first by text order (left-to-right)**
   - This ensures deterministic behavior: same input → same output
   
   **Critical rule for equal distances:**
   - When multiple matches have the same distance to `time_position`, the selection MUST be deterministic
   - Selection uses text position (character index) as secondary sort key
   - The match with the smallest text position (leftmost in text) is selected
   - This rule applies to ALL priority levels (offset strings, IANA IDs, city names)
   - Example: `"Meeting UTC+2 at 10:30 UTC+3"` → if both offsets are at equal distance from time position, use `UTC+2` (first by text order, left-to-right)
   
   **Implementation detail:**
   - Sorting uses tuple `(distance, text_position)` to guarantee deterministic selection
   - `min()` with tuple key ensures first match by text order when distances are equal
   - `text_position` is the absolute character position in the original message text
   - This guarantees that the same input always produces the same output, regardless of iteration order
   
   **Special case for offset strings:**
   - If multiple offset strings (Priority 1) are found at equal distance:
     - Use the first match by text position (left-to-right)
     - This ensures deterministic behavior even when multiple offsets appear in context
   - Example: `"Meeting UTC+2 at 10:30 UTC+3"` → if both offsets are at equal distance from time position, use `UTC+2` (first by text order)

**Examples:**
- `"10:30 Amsterdam UTC+5"` → use `UTC+5` (Priority 1 > Priority 3)
- `"10:30 Amsterdam Paris"` → use closest city to `"10:30"` position
- `"Amsterdam 10:30 Paris"` → use `"Amsterdam"` (closer to time position)
- `"Meeting UTC+2 at 10:30 UTC+3"` → if distances equal, use `UTC+2` (first by text order)

**Conflicting signals:**
- `"10:30 Amsterdam UTC+5"` → use `UTC+5` (higher priority)

**Offset strings from text:**
- Offset strings extracted from message text are treated as explicit timezones
- They bypass user/channel timezone resolution (highest priority)
- They are passed directly to converter for time conversion

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

## 6. Converter Support for Offset Strings

The converter (`convert_time`) supports both IANA timezone IDs and fixed UTC offsets.

**Supported formats:**
- IANA timezone IDs: `Europe/Amsterdam`, `America/New_York`
- Fixed UTC offsets: `+03:00`, `-05:00` (normalized format from extractor)

**Behavior for offsets:**
- Offsets are treated as fixed-offset timezones without DST
- No DST adjustment is applied (offset is constant)
- Display uses original offset string as `timezone_id` in DisplayBlock

**Example:**
- Extracted: `"+03:00"`
- Converted to: Fixed offset timezone UTC+03:00
- Display: `timezone_id = "+03:00"`

**Rationale:**
- Extractor can return offset strings (see §1.1)
- Converter must handle these offsets to maintain contract consistency
- Fixed offsets provide predictable behavior without DST complexity

**Offset strings in target_timezones:**
- Offset strings can appear in `target_timezones` list when:
  - They are resolved as `base_timezone` (explicit hint from message text)
  - They are included in conversion targets alongside IANA timezone IDs
- Converter handles offset strings identically whether they are `base_timezone` or target timezones
- Offset strings do not have associated cities in `cities.json` (only IANA IDs have city mappings)
- This creates two classes of timezones in the system:
  - **Named timezones** (IANA IDs): have cities, support DST, stable identifiers
  - **Anonymous timezones** (offset strings): no cities, fixed offset, situational hints

---

## 7. Offset Range Validation

**Requirement:** All offset strings must be validated for range before being used.

**Validation Rules:**
- **Hours:** Must be in range [0, 14]
  - UTC offsets typically range from ±12 hours
  - Allow up to ±14 hours for edge cases (e.g., Line Islands UTC+14)
  - Offsets outside this range are invalid and ignored
- **Minutes:** Must be in range [0, 59]
  - Standard timezone offsets use 0, 15, 30, or 45 minutes
  - Any value 0-59 is accepted for flexibility
  - Values outside this range are invalid and ignored

**Behavior:**
- Invalid offset strings (out of range) → return `None` from `normalize_offset()`
- No explicit hint found → resolver falls back to next priority (user profile, channel default, etc.)
- Invalid offsets are **not** converted to "+00:00" to preserve signal integrity
- This ensures system doesn't hallucinate UTC when user provides invalid offset

**Examples:**
- `"+15:00"` → Invalid (hours > 14) → `None` → no explicit hint
- `"+03:60"` → Invalid (minutes > 59) → `None` → no explicit hint
- `"+14:00"` → Valid → `"+14:00"` → explicit hint found
- `"-12:30"` → Valid → `"-12:30"` → explicit hint found

---

## 8. References

- `POLICIES.md` §1.4 — Timezone Hint Extraction
- `POLICIES.md` §3 — Timezone Resolution Precedence
- `cities.json` — City whitelist (adapter-owned)
- `CORE_CONTRACT.md` — Converter error handling

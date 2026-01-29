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
| `+3` | `+03:00` |
| `+03:30` | `+03:30` |
| `-05:30` | `-05:30` |

**Supported formats:**
- Hour only: `+3`, `+03`, `-5`, `-05`
- Hour with colon-separated minutes: `+03:00`, `+03:30`, `-05:30`
- With UTC/GMT prefix: `UTC+2`, `GMT-5`, `UTC+03:00`

**NOT supported (MVP):**
- Compact 4-digit format without colon: `+0300`, `+0530` (only first 2 digits after sign are matched)

**Rules:**
- Case-insensitive (`utc`, `UTC`, `Utc` all valid)
- Normalize to `±HH:MM` format internally
- To specify non-zero minutes, use colon-separated format (e.g., `+03:30`)

---

### 1.2 Explicit IANA Timezone ID

**Pattern:** `[A-Za-z_]+/[A-Za-z_]+`

**Supported IANA IDs (MVP):**
- Only **two-segment** IDs: `Region/City`
- Examples: `Europe/Amsterdam`, `Asia/Yerevan`, `America/New_York`

**NOT Supported (MVP):**
- Multi-segment IDs: `America/Argentina/Buenos_Aires`
- `Etc/GMT+X` offsets: `Etc/GMT+0`, `Etc/GMT-5`

**Rationale:** MVP focuses on human-used timezones only. Complex IANA IDs
like `America/Argentina/Buenos_Aires` or `Etc/GMT+X` are rarely used in
casual conversation and can be added post-MVP if needed.

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
- No morphological matching (e.g., Russian "Москва" ≠ "Москве" - different word forms)

**Examples:**
| Input | Match? |
|-------|--------|
| `"in Amsterdam"` | ✅ Yes |
| `"amsterdam"` | ✅ Yes |
| `"AMSTERDAM"` | ✅ Yes |
| `"Amsterdamn"` | ❌ No (typo) |
| `"New Amsterdam"` | ❌ No (not in whitelist) |
| `"New York"` | ✅ Yes (multi-word phrase) |
| `"St. Petersburg"` | ✅ Yes (with dot normalization) |
| `"St Petersburg"` | ✅ Yes (normalized to same as above) |
| `"Saint-Petersburg"` | ✅ Yes (hyphen supported) |
| `"The Hague"` | ✅ Yes (multi-word phrase) |

### 1.4 Supported City Name Character Set and Normalization Rules

**Character Set:**
City names support the following characters:
- **Unicode word characters** (`\w`): All Unicode letters, Unicode decimal digits, and underscore (`_`)
  - Includes ASCII letters (`A-Z`, `a-z`), ASCII digits (`0-9`), and underscore
  - Also includes all Unicode letters from any language (e.g., `Москва`, `São Paulo`, `北京`)
  - Also includes Unicode decimal digits from any script (e.g., `٠١٢٣` Arabic-Indic digits)
- **Hyphens** (`-`): For compound city names (e.g., `Saint-Petersburg`, `Buenos-Aires`)
- **Dots** (`.`): For abbreviations (e.g., `St. Petersburg`, `Dr.`, `Mt.`)

**Note:** The pattern uses `re.UNICODE` flag (default in Python 3), which makes `\w` match the full Unicode word character set, not just ASCII.

**Tokenization Pattern:**
```
\b[\w.-]+\b
```

**Supported Formats:**

The system **explicitly supports** the following city name formats:

1. **Words with hyphens:**
   - `Saint-Petersburg`, `Buenos-Aires`, `Saint-Denis`

2. **Words with dots:**
   - `St.`, `Dr.`, `Mt.`
   - Dots are normalized (removed) for flexible matching
   - `St. Petersburg` matches `St Petersburg`

3. **Multi-word phrases:**
   - `New York`, `The Hague`, `St. Petersburg`
   - Phrases are matched as complete sequences (2-word and 3-word)

**Not Supported:**

All other punctuation (commas, apostrophes, etc.) acts as word boundaries and breaks tokenization.

**CJK Language Handling:**

- Spaces between words are required for tokenization
- Languages without spaces (Chinese, Japanese, Thai) require explicit spaces
  around city names
- Exact match only, no morphological segmentation

Examples:
- `"会议 北京 10:00"` → supported (spaces present around city name)
- `"会议北京10:00"` → not supported (no spaces, city name not tokenized)

**Normalization Rules:**

1. **Case Normalization:**
   - All city name matching is case-insensitive
   - Input is converted to lowercase before lookup
   - Example: `"Amsterdam"`, `"AMSTERDAM"`, `"amsterdam"` → all match `"amsterdam"` in index

2. **Dot Normalization (Abbreviation Handling):**
   - Dots in abbreviations are normalized (removed) for flexible matching
   - This allows `"St. Petersburg"` and `"St Petersburg"` to match the same city
   - Normalization function: `text.lower().replace('.', '')`
   - Example: `"St. Petersburg"` → normalized to `"st petersburg"` for lookup

3. **Multi-word Phrase Matching:**
   - Cities with spaces are matched as complete phrases
   - Phrases are checked as 2-word and 3-word sequences
   - Examples:
     - `"New York"` → matched as phrase `"new york"`
     - `"St. Petersburg"` → normalized to `"st petersburg"` → matched as phrase
     - `"The Hague"` → matched as phrase `"the hague"`

**Index Construction:**
At startup, the adapter builds a city index with both exact and normalized keys:

```python
def normalize_city_key(text: str) -> str:
    """Normalize city name by removing dots for abbreviation matching."""
    return text.lower().replace('.', '')

city_index = {}
for entry in cities_json:
    city = entry["city"]
    city_lower = city.lower()
    city_normalized = normalize_city_key(city)
    
    # Store exact match (preserves original form)
    city_index[city_lower] = entry["timezone"]
    
    # Store normalized match (for abbreviations)
    if city_normalized != city_lower:
        city_index[city_normalized] = entry["timezone"]
```

**Matching Examples:**

| Input Text | Tokenized | Normalized Lookup | Match Result |
|------------|-----------|-------------------|--------------|
| `"Meeting at 10:00 Amsterdam"` | `["Meeting", "at", "10:00", "Amsterdam"]` | `"amsterdam"` | ✅ `Europe/Amsterdam` |
| `"Call at 14:00 New York"` | `["Call", "at", "14:00", "New", "York"]` | `"new york"` | ✅ `America/New_York` |
| `"Sync at 9:00 St. Petersburg"` | `["Sync", "at", "9:00", "St.", "Petersburg"]` | `"st petersburg"` | ✅ `Europe/Moscow` (if in index) |
| `"Meeting at 10:00 St Petersburg"` | `["Meeting", "at", "10:00", "St", "Petersburg"]` | `"st petersburg"` | ✅ `Europe/Moscow` (same as above) |
| `"Call at 14:00 Saint-Petersburg"` | `["Call", "at", "14:00", "Saint-Petersburg"]` | `"saint-petersburg"` | ✅ `Europe/Moscow` (if in index) |
| `"Sync at 9:00 The Hague"` | `["Sync", "at", "9:00", "The", "Hague"]` | `"the hague"` | ✅ `Europe/Amsterdam` (if in index) |



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
| `country` | string | no | ISO 3166-1 alpha-2 country code (metadata only) |
| `timezone` | string | yes | IANA timezone ID |
| `aliases` | string[] | no | Alternative names (may be empty) |

**Rules:**
- Each city/alias appears in exactly one entry
- No duplicates across entries
- Adapter loads this file at startup

**Duplicate handling:**

- If a city or alias appears multiple times, last entry wins (dict semantics)
- This is undefined behavior; data should be validated to avoid duplicates
- Adapter may log a warning but continues operation

**Error Handling for cities.json:**

If `cities.json` is invalid:
- **JSON parse error** → adapter fails to start (fatal error, logged)
- **Missing required fields in entries** → entry skipped with warning log
- **Invalid timezone in entry** (not in `zoneinfo.available_timezones()`) → entry skipped with warning
- **Entire file empty `[]`** → valid state, city extraction disabled

Required fields per entry: `city`, `timezone`. Optional: `country`, `aliases`.

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

At startup, adapter builds a lookup index for O(1) matching with normalization support:

```python
def normalize_city_key(text: str) -> str:
    """Normalize city name by removing dots for abbreviation matching."""
    return text.lower().replace('.', '')

city_index: Dict[str, str] = {}  # lowercase name → timezone

for entry in cities_json:
    city = entry["city"]
    city_lower = city.lower()
    city_normalized = normalize_city_key(city)
    
    # Store exact match (preserves original form)
    city_index[city_lower] = entry["timezone"]
    
    # Store normalized match (for abbreviations like "St." -> "st")
    if city_normalized != city_lower:
        city_index[city_normalized] = entry["timezone"]
    
    # Same for aliases
    for alias in entry["aliases"]:
        alias_lower = alias.lower()
        alias_normalized = normalize_city_key(alias)
        city_index[alias_lower] = entry["timezone"]
        if alias_normalized != alias_lower:
            city_index[alias_normalized] = entry["timezone"]
```

**Usage:**
The extraction algorithm uses the normalized lookup function when matching phrases:

```python
def normalize_for_lookup(text: str) -> str:
    """Normalize text by removing dots for abbreviation matching."""
    return text.lower().replace('.', '')

# Single word check
if word.lower() in city_index or normalize_for_lookup(word) in city_index:
    return city_index[word.lower()] or city_index[normalize_for_lookup(word)]

# Multi-word phrase check
phrase_normalized = normalize_for_lookup(phrase)
if phrase in city_index or phrase_normalized in city_index:
    return city_index[phrase] or city_index[phrase_normalized]
```

**Index Structure:**
- Keys are lowercase city names (exact and normalized)
- Values are IANA timezone IDs
- Both exact and normalized keys point to the same timezone
- Example: `{"st. petersburg": "Europe/Moscow", "st petersburg": "Europe/Moscow"}`

---

## 3. Matching Algorithm

### 3.1 Tokenization

```python
def tokenize(text: str) -> List[str]:
    """
    Split text into word tokens.
    Uses word boundaries, preserves Unicode letters, hyphens, and dots.
    Lowercasing is done during comparison, not here.
    
    Pattern: \b[\w.-]+\b captures:
    - Unicode letters (\w): A-Z, a-z, 0-9, _, and Unicode letters
    - Hyphens (-): for compound names like "Saint-Petersburg"
    - Dots (.): for abbreviations like "St.", "Dr.", "Mt."
    """
    return re.findall(r'\b[\w.-]+\b', text, re.UNICODE)
```

**Examples:**
- `"in Amsterdam"` → `["in", "Amsterdam"]`
- `"10:30 UTC+2"` → `["10", "30", "UTC", "2"]`
- `"see you в Москве"` → `["see", "you", "в", "Москве"]`
- `"Meeting at 10:00 St. Petersburg"` → `["Meeting", "at", "10:00", "St.", "Petersburg"]`
- `"Call in Saint-Petersburg"` → `["Call", "in", "Saint-Petersburg"]`

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

**Invalid format note:**
- Multiple leading signs (e.g., `"++03:00"` or `"--05:00"`) are invalid and must return `None`.

**Examples:**
- `"+3"` → `"+03:00"`
- `"UTC+2"` → `"+02:00"`
- `"+0300"` → `"+03:00"` (not matched in extraction per D-001; normalization semantics only)
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
        time_position: Start position of the time mention (DetectedTime.position_start from TIME_PARSING_RULES)
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
    # (?!\d) prevents matching compact +0300 (D-001): only colon-separated or hour-only
    TZ_OFFSET_REGEX = re.compile(r'(UTC|GMT)?[+-]\d{1,2}(:\d{2})?(?!\d)', re.IGNORECASE)
    offset_matches = list(TZ_OFFSET_REGEX.finditer(context))
    if offset_matches:
        valid_offsets = []
        for match in offset_matches:
            normalized = normalize_offset(match.group())
            if normalized:
                valid_offsets.append((match, normalized))
        if valid_offsets:
            closest_match, normalized = min(
                valid_offsets,
                key=lambda item: (abs((start + item[0].start()) - time_position), item[0].start())
            )
            return normalized
    
    # Priority 2: IANA timezone ID
    TZ_IANA_REGEX = re.compile(r'\b[A-Za-z_]+/[A-Za-z_]+\b')
    iana_matches = list(TZ_IANA_REGEX.finditer(context))
    if iana_matches:
        valid_matches = []
        for match in iana_matches:
            tz_id = match.group()
            if tz_id in zoneinfo.available_timezones():
                valid_matches.append((match, tz_id))
        if valid_matches:
            closest_match, tz_id = min(
                valid_matches,
                key=lambda item: (abs((start + item[0].start()) - time_position), item[0].start())
            )
            return tz_id
    
    # Priority 3: City lookup (uses passed index)
    # Supports single words, multi-word phrases, and normalization
    word_pattern = re.compile(r'\b[\w.-]+\b', re.UNICODE)
    
    def normalize_for_lookup(text: str) -> str:
        """Normalize text by removing dots for abbreviation matching."""
        return text.lower().replace('.', '')
    
    # Check single words (exact and normalized)
    city_matches = []
    for match in word_pattern.finditer(context):
        word = match.group()
        word_normalized = normalize_for_lookup(word)
        if word.lower() in city_index:
            city_matches.append((match.start(), city_index[word.lower()], 1))
        elif word_normalized in city_index:
            city_matches.append((match.start(), city_index[word_normalized], 1))
    
    # Check multi-word phrases (2-word and 3-word)
    words_list = word_pattern.findall(context)
    for i in range(len(words_list) - 1):
        phrase_2 = f"{words_list[i]} {words_list[i+1]}".lower()
        phrase_2_normalized = normalize_for_lookup(phrase_2)
        if phrase_2 in city_index:
            city_matches.append((words_positions[i][0], city_index[phrase_2], 2))
        elif phrase_2_normalized in city_index:
            city_matches.append((words_positions[i][0], city_index[phrase_2_normalized], 2))
    
    for i in range(len(words_list) - 2):
        phrase_3 = f"{words_list[i]} {words_list[i+1]} {words_list[i+2]}".lower()
        phrase_3_normalized = normalize_for_lookup(phrase_3)
        if phrase_3 in city_index:
            city_matches.append((words_positions[i][0], city_index[phrase_3], 3))
        elif phrase_3_normalized in city_index:
            city_matches.append((words_positions[i][0], city_index[phrase_3_normalized], 3))
    
    if city_matches:
        longest_by_start = {}
        for pos, tz_id, word_count in city_matches:
            current = longest_by_start.get(pos)
            if current is None or word_count > current[2]:
                longest_by_start[pos] = (pos, tz_id, word_count)
        filtered_matches = list(longest_by_start.values())
        closest_pos, tz_id, _ = min(
            filtered_matches,
            key=lambda item: (abs((start + item[0]) - time_position), item[0])
        )
        return tz_id
    
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

**Window calculation clarification:**
- Window is centered around the **start position** of the time mention (same as `DetectedTime.position_start` from TIME_PARSING_RULES; not center or end of the time span)
- Formula: `start = max(0, time_position - 30)`, `end = min(len(text), time_position + 30)`
- For time mention "10:30" at position 20: window is `[0:50]` (characters 0-49)
- Window may be asymmetric at text boundaries (beginning or end of message)

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
| Other punctuation | Commas, apostrophes, etc. | Act as word boundaries and break tokenization |

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

- `POLICIES.md` §2 — Timezone Extraction Policy
- `POLICIES.md` §3 — Timezone Resolution Precedence
- `TIME_PARSING_RULES.md` — time positions (position_start, position_end) feed into time_position
- `cities.json` — City whitelist (adapter-owned)
- `CORE_CONTRACT.md` — Converter error handling

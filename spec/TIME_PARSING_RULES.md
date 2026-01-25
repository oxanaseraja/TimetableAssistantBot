# TIME_PARSING_RULES.md — MVP Absolute Time Grammar

This document defines the **input contract** for time parsing.
Only patterns listed here are recognized. Everything else is ignored.

Time parsing is **regex-based only**. No LLM, no heuristics, no guessing.

---

## 1. Supported Patterns (Priority Order)

Patterns are applied in order. First match wins.

### 1.1 TIME_24H — Colon-separated 24-hour format

**Regex:** `\b([01]?\d|2[0-3]):([0-5]\d)\b`

| Example | hour | minute | ambiguous |
|---------|------|--------|-----------|
| `10:30` | 10 | 30 | false |
| `09:05` | 9 | 5 | false |
| `23:59` | 23 | 59 | false |
| `0:00` | 0 | 0 | false |

**Ambiguity:** Never ambiguous (24h format is explicit).

---

### 1.2 TIME_12H_AMPM — 12-hour format with AM/PM

**Regex:** `\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(am|pm|AM|PM|a\.m\.|p\.m\.)\b`

**Note:** Non-capturing group `(?:...)` for colon ensures group(2) captures only digits.

| Example | hour | minute | am_pm | ambiguous |
|---------|------|--------|-------|-----------|
| `1pm` | 1 | null | PM | false |
| `10:30am` | 10 | 30 | AM | false |
| `9 AM` | 9 | null | AM | false |
| `12:00 p.m.` | 12 | 0 | PM | false |

**Ambiguity:** Never ambiguous (AM/PM is explicit).

**Conversion to 24h:**
- 12am → 00:00
- 12pm → 12:00
- 1pm-11pm → 13:00-23:00

---

### 1.3 TIME_BARE_HOUR — Hour only with trigger word

**Trigger words (case-insensitive):**
- English: `at`, `by`, `around`, `about`, `until`, `till`
- Russian: `в`, `к`, `около`, `до`

**Full Regex:**

```python
TRIGGER_WORDS = r'(?:at|by|around|about|until|till|в|к|около|до)'
TIME_BARE_HOUR_REGEX = re.compile(
    rf'(?i)\b({TRIGGER_WORDS})\s+([1-9]|1[0-2])\b',
    re.UNICODE
)
```

**Examples:**

| Example | hour | minute | ambiguous |
|---------|------|--------|-----------|
| `at 8` | 8 | null | **true** |
| `At 8` | 8 | null | **true** |
| `в 10` | 10 | null | **true** |
| `by 3` | 3 | null | **true** |

**Ambiguity:** Always ambiguous (no AM/PM, could be 08:00 or 20:00).

**Behavior:** Core returns `ambiguity: HIGH` → adapter sends no reply.

**Note:** Trigger word is captured in group(1), hour in group(2).

---

## 2. Unsupported Patterns (Explicitly Ignored)

These formats are **NOT recognized** in MVP:

| Format | Example | Reason |
|--------|---------|--------|
| Dot separator | `10.30` | Conflicts with decimals, versions (`v10.30`) |
| European `h` | `10h30` | Not common in target locales |
| Word-based | `half past 10` | Requires NLP |
| Relative | `in 2 hours`, `через час` | Requires current time context |
| Ranges | `10:00-11:00` | Out of scope |
| Date+time | `Jan 25 at 10:30` | Out of scope |
| ISO 8601 | `2026-01-25T10:30:00Z` | Out of scope |

**Note:** Dot-separated time format (HH.MM) is explicitly NOT supported in MVP.
Rationale: ambiguity with decimal numbers and version strings.

---

## 3. Parsing Algorithm

### 3.1 Overlap Detection

Positions are **half-open intervals** `[start, end)` on the original string.

```python
def overlaps(match, existing_results: List[DetectedTime]) -> bool:
    """
    Check if match overlaps with any existing result.
    Positions are character indices in the original string.
    """
    for r in existing_results:
        # Overlap if intervals intersect
        if not (match.end() <= r.position_start or match.start() >= r.position_end):
            return True
    return False
```

### 3.2 Main Algorithm

```python
def parse_times(text: str, max_results: int = 3) -> List[DetectedTime]:
    """
    Parse time mentions from text.
    
    Args:
        text: Message text to parse
        max_results: Maximum times to return (default: 3, from CoreConfig)
    
    Returns:
        List of DetectedTime, sorted by position, capped to max_results
    """
    results = []
    
    # Priority 1: TIME_24H
    for match in TIME_24H_REGEX.finditer(text):
        results.append(DetectedTime(
            raw_text=match.group(),
            hour=int(match.group(1)),
            minute=int(match.group(2)),
            am_pm=None,
            position_start=match.start(),
            position_end=match.end(),
            ambiguous=False
        ))
    
    # Priority 2: TIME_12H_AMPM (skip if overlaps with existing)
    # Regex: \b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(am|pm|...)\b
    # Groups: (1)=hour, (2)=minute (digits only, no colon), (3)=am/pm
    for match in TIME_12H_AMPM_REGEX.finditer(text):
        if not overlaps(match, results):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else None  # group(2) is digits only
            am_pm = match.group(3).upper().replace('.', '')  # Normalize "a.m." → "AM"
            results.append(DetectedTime(
                raw_text=match.group(),
                hour=hour,
                minute=minute,
                am_pm=am_pm,
                position_start=match.start(),
                position_end=match.end(),
                ambiguous=False
            ))
    
    # Priority 3: TIME_BARE_HOUR (skip if overlaps)
    for match in TIME_BARE_HOUR_REGEX.finditer(text):
        if not overlaps(match, results):
            results.append(DetectedTime(
                raw_text=match.group(),
                hour=int(match.group(2)),  # group(1) is trigger word
                minute=None,
                am_pm=None,
                position_start=match.start(),
                position_end=match.end(),
                ambiguous=True  # Always ambiguous
            ))
    
    # Sort by position, cap to max_results
    return sorted(results, key=lambda x: x.position_start)[:max_results]
```

---

## 4. Edge Cases

| Input | Matches | Notes |
|-------|---------|-------|
| `"10:30"` | `[10:30]` | Single match |
| `"at 10:30"` | `[10:30]` | TIME_24H wins over bare hour |
| `"see you at 8"` | `[8]` (ambiguous) | Bare hour, triggers ambiguity |
| `"v10.30"` | `[]` | Not matched (dot format) |
| `"10:30, 11:00, 12:00, 13:00"` | `[10:30, 11:00, 12:00]` | Capped to 3 |
| `"call at 10am or 2pm"` | `[10am, 2pm]` | Both matched |

---

## 5. References

- `POLICIES.md` §1 — Time Detection Policy (behavioral rules)
- `POLICIES.md` §4 — Ambiguity Policy (what happens when ambiguous)
- `CONTRACTS.md` — `DetectedTime` DTO structure

# Test Phrases for TimetableAssistantBot

This document contains example messages for testing bot behavior.

---

## ✅ Successful tests (bot should reply)

### 1. Time with explicit UTC/GMT offset

```
Meeting at 10:30 UTC+3
Call at 14:00 UTC+2
Standup at 9:00am GMT-5
Daily sync at 15:30 +03:00
```

**Expected behavior:** Bot converts time to the given offset and shows other timezones.

---

### 2. Time with city name

```
See you at 10:30 pm Amsterdam
Call at 14:00 London
Meeting at 9:00am New York
Standup at 15:30 Moscow
Daily sync at 11:00 Tokyo
```

**Expected behavior:** Bot recognizes city, resolves timezone, and converts time.

**Available cities** (from `cities.json`): see `src/data/cities.json` or `docs/data/cities.json`.

---

### 3. Time with IANA timezone ID

```
Meeting at 10:30 Europe/Amsterdam
Call at 14:00 America/New_York
Standup at 9:00am Asia/Tokyo
Daily sync at 15:30 Europe/Moscow
```

**Expected behavior:** Bot uses the given IANA timezone ID directly.

---

### 4. 24-hour format

```
Meeting at 10:30
Call at 14:00
Standup at 09:00
Daily sync at 23:30
```

**Expected behavior:** Bot recognizes 24-hour format and converts time.

---

### 5. 12-hour format with AM/PM

```
Meeting at 10:30am
Call at 2:00pm
Standup at 9 AM
Daily sync at 11:30 PM
Review at 12:00 p.m.
```

**Expected behavior:** Bot converts to 24-hour format and shows in different timezones.

---

### 6. Time without minutes (hour only)

```
Meeting at 10am
Call at 2pm
Standup at 9 AM
Daily sync at 11 PM
```

**Expected behavior:** Bot treats as 10:00, 14:00, etc.

---

### 7. Time without explicit timezone (uses user profile)

```
Meeting at 10:30
Call at 14:00
Standup at 9:00am
```

**Expected behavior:**
- If user has timezone in `users.json` → use it
- Else → channel default timezone
- Else → if exactly one active timezone in group → use it; else → SYSTEM_DEFAULT (UTC) or no reply (ambiguity)

---

### 8. Bare hour with trigger word

```
See you at 8
Call at 10
Meeting at 3
```

**Note:** These are ambiguous (no AM/PM); bot does not reply. Expected behavior.

---

### 9. Time and city in different positions

```
Amsterdam meeting at 10:30
Call at 14:00 in London
Standup at 9:00am New York time
Meeting Amsterdam 10:30
```

**Expected behavior:** Bot finds city within ±30 characters of the time mention.

---

### 10. Multiple time mentions (up to 3)

```
Meeting at 10:30 and call at 14:00
Standup at 9am, review at 11am, sync at 3pm
```

**Expected behavior:** Bot processes only the first time (MVP simplification).

---

## ❌ Tests that should be ignored (bot does not reply)

### 1. Ambiguous time (bare hour without AM/PM)

```
See you at 8
Call at 10
Meeting at 3
```

**Expected behavior:** Bot does not reply (ambiguous: could be 08:00 or 20:00).

---

### 2. More than 3 time mentions

```
Meeting at 10, call at 11, sync at 12, review at 13, standup at 14
```

**Expected behavior:** Only the first time is processed; excess mentions are not used (see SPEC_FREEZE §3.1).

---

### 3. No time in message

```
Hello everyone!
How are you?
Let's meet tomorrow
```

**Expected behavior:** Bot does not reply (no time to process).

---

### 4. Commands (start with /)

```
/start
/help
/settimezone
```

**Expected behavior:** Bot does not reply (commands are out of scope or filtered).

---

### 5. Unsupported time formats

```
Meeting at 10.30        (dot instead of colon — not supported)
Call at 10h30          (European 'h' format — not supported)
See you half past 10   (word-based — not supported)
Meeting tomorrow at 10 (relative time — not supported)
```

**Expected behavior:** Bot does not reply (format not recognized).

---

### 6. Unknown city

```
Meeting at 10:30 in UnknownCity
Call at 14:00 Somewhere
```

**Expected behavior:**
- If another timezone hint exists → use it
- Else → use profile/channel default
- Else → ambiguity → no reply

---

## 🧪 Edge cases

### 1. Boundary times

```
Meeting at 00:00        (midnight)
Call at 23:59          (end of day)
Standup at 12:00pm     (noon)
Review at 12:00am      (midnight in 12h format)
```

---

### 2. Different offset formats

```
Meeting at 10:30 UTC+3
Call at 14:00 +03:00
Standup at 9:00am GMT-5
Sync at 15:30 -05:00
```

**Note:** Compact format `+0300` (no colon) is not supported (SPEC_FREEZE D-001). Use `+03:00` or `UTC+3`.

---

### 3. Message edit

1. Send: `Meeting at 10:00`
2. Edit to: `Meeting at 11:00`

**Expected behavior:** Old reply is deleted; new reply is sent.

---

### 4. Empty users.json (no profiles)

If `users.json` is empty or user is not in the list:

```
Meeting at 10:30 Amsterdam
```

**Expected behavior:** Uses explicit hint (Amsterdam) or SYSTEM_DEFAULT.

---

### 5. Multiple active timezones in group

If the group has several members with different timezones and no explicit hint:

```
Meeting at 10:30
```

**Expected behavior:** Ambiguity → no reply (per POLICIES §3, §4).

---

## 📋 Testing checklist

- [ ] 24-hour format (10:30)
- [ ] 12-hour format with AM/PM (10:30am, 2:00pm)
- [ ] Hour without minutes (10am, 2pm)
- [ ] Explicit UTC offset (UTC+3, +03:00)
- [ ] City name (Amsterdam, London, New York)
- [ ] IANA timezone ID (Europe/Amsterdam)
- [ ] Time without timezone (uses profile)
- [ ] Ambiguous time (at 8 — should be ignored)
- [ ] Multiple time mentions (first only in MVP)
- [ ] Message edit (old reply removed)
- [ ] Commands (ignored)
- [ ] Messages without time (ignored)

---

## References

- `TIME_PARSING_RULES.md` — supported time formats
- `TIMEZONE_EXTRACTION_RULES.md` — timezone hint extraction
- `POLICIES.md` §4 — ambiguity policy
- `END_TO_END_FLOW.md` — step-by-step example

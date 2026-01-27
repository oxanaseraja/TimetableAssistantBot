# USER_PROFILE_MODEL.md — MVP User Timezone Source

This document defines how user timezone information is acquired and used.

---

## 1. Core Principle

**Core does not own user data.**

Core receives `UserProfile` as input from adapter.
Core never stores, modifies, or queries user data directly.

---

## 2. UserProfile Structure (MVP)

```
UserProfile {
    internal_user_id: string,   # SHA256 hash (see POLICIES.md §8)
    timezone: string | null     # IANA timezone ID or null
}
```

**Critical constraint:**
- **Only IANA timezone IDs are allowed** in `timezone` field
- **Offset strings (`±HH:MM`) are NOT allowed** in user profiles
- **Offset strings (`±HH:MM`) are NOT allowed** in `users.json` file
- Offset strings may appear **only** as explicit hints extracted from message text
- Invalid timezone IDs are treated as `null` (missing timezone)

**Why offset strings are not allowed:**
- Profiles represent stable, persistent user data
- Offset strings are situational hints from message text
- Offset strings don't carry DST information
- Offset strings cannot be validated via `zoneinfo.available_timezones()`
- This separation ensures data integrity and predictable behavior

Only `timezone` field is used in MVP.
Additional fields (name, language, etc.) are out of scope.

---

## 3. Source of UserProfile (MVP)

In MVP, user profiles are loaded from a **static JSON file**.

### File: `users.json`

```json
{
  "telegram:123456789": {
    "timezone": "Europe/Amsterdam"
  },
  "telegram:987654321": {
    "timezone": "Asia/Yerevan"
  }
}
```

**Structure:**
- Key: `{platform}:{platform_user_id}` (before hashing)
- Value: Object with `timezone` field

**Why this format:**
- Adapter hashes key to get `internal_user_id`
- Simple lookup
- Easy to edit manually for testing

---

## 4. Adapter Responsibilities

### On startup:
1. Load `users.json` if exists
2. Build in-memory map: `platform_user_id → timezone`
3. Handle errors according to error handling policy (see below)

### users.json Error Handling

| Condition | Behavior |
|-----------|----------|
| Missing file | Treated as empty map `{}` — adapter starts normally |
| Empty file `{}` | Treated as empty map `{}` — adapter starts normally |
| Invalid JSON (parse error) | **Fatal error** — adapter fails to start |
| Permission denied | **Fatal error** — adapter fails to start |
| Invalid structure (not a dict) | Treated as empty map `{}` with warning |

**Rationale:** Configuration errors must fail fast. Invalid JSON or permission issues
indicate misconfiguration that should be fixed before the adapter can operate correctly.

### Empty or Missing users.json behavior:

Both cases are treated identically:
- Missing file → empty map `{}`
- Empty file `{}` → empty map `{}`
- System starts normally with no user/channel data

In this case:
- All users have `timezone = None`
- All channels have `default_timezone = None`
- `active_timezones` may be empty

System behavior:
- Resolution relies on explicit timezone hints in text (see `TIMEZONE_EXTRACTION_RULES.md`)
- Or `SYSTEM_DEFAULT` if configured
- If no timezone can be resolved → no reply is sent (ambiguity)

**Rationale:**
- Bot is voluntary helper, not all users fill profiles
- System gracefully degrades to explicit hints
- Matches MVP product model: "bot learns timezones" (not "must know")

### On message:
1. Lookup sender's timezone from in-memory map
2. Construct `UserProfile` DTO
3. Pass to core as part of context

### Hashing:
```python
internal_user_id = sha256(f"telegram:{platform_user_id}").hexdigest()
```

---

## 5. Fallback Behavior

If user timezone is unknown (not in `users.json`):

1. `UserProfile.timezone = null`
2. Core skips "User profile timezone" in resolution precedence
3. Falls back to:
   - Channel default timezone, OR
   - Single active timezone, OR
   - Ambiguity (no reply)

**Core never guesses user timezone.**

---

## 6. ChannelContext Structure (MVP)

```
ChannelContext {
    internal_channel_id: string,
    default_timezone: string | null,
    active_timezones: List<string>
}
```

### Source of ChannelContext

In MVP, channel context is also loaded from `users.json`:

```json
{
  "telegram:123456789": {
    "timezone": "Europe/Amsterdam"
  },
  "channel:-1001234567890": {
    "default_timezone": "Europe/Amsterdam",
    "members": ["telegram:123456789", "telegram:987654321"]
  }
}
```

---

## 6.1 Computing active_timezones

**Definition:** `active_timezones` = unique non-null timezones of all channel members.

**Algorithm:**

```python
def compute_active_timezones(
    channel_config: dict,
    user_configs: Dict[str, dict]
) -> List[str]:
    """
    Active timezones = unique non-null timezones of all channel members
    known at message time.
    
    Computed on every message. Not cached globally.
    """
    timezones = set()
    
    for member_key in channel_config.get("members", []):
        user = user_configs.get(member_key)
        if user and user.get("timezone"):
            timezones.add(user["timezone"])
    
    # Sorted for determinism
    return sorted(list(timezones))
```

**Rules:**
- Recomputed on every message (not cached)
- Source of truth: ChannelContext.members + UserProfile.timezone
- Unknown members are ignored (not an error)
- Null timezones are excluded
- Result is sorted alphabetically for determinism

---

## 7. Out of Scope (MVP)

| Feature | Status | Notes |
|---------|--------|-------|
| `/settimezone` command | ❌ Out of scope | No user interaction |
| Auto-detection from Telegram | ❌ Out of scope | Privacy concerns |
| GeoIP detection | ❌ Out of scope | Unreliable |
| Timezone learning from messages | ❌ Out of scope | Too complex |
| Activity-based decay | ❌ Out of scope | Requires persistent storage |

---

## 8. Future Extensions

For production, consider:
- Database storage (PostgreSQL, Redis)
- `/settimezone` command
- Admin panel for bulk management
- Timezone inference from message patterns

These are explicitly **not part of MVP**.

---

## 9. Timezone ID Validation

**Requirement:** All timezone IDs in `users.json` must be valid IANA timezone identifiers.

**Critical constraint:**
- **Only IANA timezone IDs are allowed** in `users.json` and channel profiles
- **Offset strings (`±HH:MM`) are NOT allowed** in:
  - User profiles (`timezone` field)
  - Channel `default_timezone`
  - `active_timezones` list

**Offset strings:**
- May appear **only** as explicit hints extracted from message text
- Are handled by extractor (see `TIMEZONE_EXTRACTION_RULES.md` §1.1)
- Bypass user/channel timezone resolution (highest priority)

**Rationale:**
- Profiles = stable, persistent data
- Offset = situational hint from text
- Offset doesn't carry DST information
- Offset cannot be validated via `zoneinfo.available_timezones()`
- This separation ensures data integrity and predictable behavior

**Validation rules:**
- Timezone IDs are validated against `zoneinfo.available_timezones()`
- Validation occurs at configuration load time (adapter startup)
- Validation occurs when processing user profiles and channel contexts
- **Offset strings (`±HH:MM`) are explicitly rejected** before IANA validation
- Offset strings are detected using regex pattern `^[+-]\d{2}:\d{2}$` and rejected with warning

**Behavior for invalid timezone IDs:**
- Invalid `default_timezone` in config → treated as `None` (UTC fallback)
- Invalid `timezone` in user profile → treated as `None` (missing timezone)
- Invalid `default_timezone` in channel context → treated as `None`
- Invalid timezone in `active_timezones` → excluded from list
- **Offset strings in any field** → explicitly rejected with warning, treated as `None` or excluded

**Error handling:**
- Validation errors are logged
- Invalid timezones are silently ignored (treated as missing)
- Offset strings trigger explicit warning messages before rejection
- Adapter continues operation with valid timezones only

**Rationale:**
- Ensures only valid IANA timezones are used
- Prevents runtime errors from invalid configuration
- Graceful degradation: invalid entries don't break entire system

---

## 10. Layer Isolation

**Critical constraint:**

`users.json` is adapter responsibility.
Core never accesses or loads this file directly.

Core receives `UserProfile` and `ChannelContext` as function arguments.
Core has no knowledge of where this data comes from.

This ensures:
- Core is testable in isolation
- Core is platform-agnostic
- Data source can change without affecting core

---

## 11. References

- `POLICIES.md` §3 — Timezone Resolution Precedence
- `POLICIES.md` §5 — Active Timezones Policy
- `CONTRACTS.md` — DTO definitions
- `ARCHITECTURAL_INVARIANTS.md` — system invariants

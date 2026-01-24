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
3. If file missing or invalid → start with empty map

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

## 9. Layer Isolation

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

## 10. References

- `POLICIES.md` §3 — Timezone Resolution Precedence
- `POLICIES.md` §5 — Active Timezones Policy
- `CONTRACTS.md` — DTO definitions
- `ARCHITECTURAL_INVARIANTS.md` — system invariants

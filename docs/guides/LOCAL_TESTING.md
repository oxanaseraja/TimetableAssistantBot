# Local Testing Guide

This guide helps you run and test TimetableAssistantBot locally with your Telegram data.

---

## Step 1: Get bot token

1. Open Telegram and find [@BotFather](https://t.me/botfather)
2. Send `/newbot` (to create a new bot) or `/token` (for an existing one)
3. Follow BotFather instructions
4. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Important:** Keep the token secret and out of git (use `.env`; see `.gitignore`).

---

## Step 2: Get group chat_id

Ways to get your group's `chat_id`:

### Option 1: Via @userinfobot

1. Add [@userinfobot](https://t.me/userinfobot) to your group
2. The bot will show the group ID (negative for groups, e.g. `-1001234567890`)

### Option 2: Via @getidsbot

1. Add [@getidsbot](https://t.me/getidsbot) to your group
2. Send any message in the group
3. The bot replies with the group ID

### Option 3: Via Telegram API

1. Create a test bot via @BotFather
2. Add it to the group
3. Send a message in the group
4. Open in browser: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find `"chat":{"id":-1001234567890}` in the response

**Note:** Group IDs are always negative (typically starting with `-100`).

---

## Step 3: Get user_id for group members

To configure `users.json` you need user IDs:

1. Add [@userinfobot](https://t.me/userinfobot) to the group, or
2. Users can send `/start` to the bot in private to get their ID, or
3. Use [@getidsbot](https://t.me/getidsbot) in the group

**Format in users.json:** `telegram:123456789` (where `123456789` is the user_id).

---

## Step 4: Configure .env

1. Create `.env` with required variables (see below).
   - If you run **from project root** (`python src/main.py`): put `.env` in the project root (next to `src/`).
   - If you run **from `src/`** (`./run.sh`): put `.env` in `src/` (or the adapter will not load it).
2. If not, create it: `touch .env` (in the directory you use to run the bot).
3. Add required variables:

**Example `.env`:**
```
# Required
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890

# Optional (defaults used if omitted)
# DATA_CITIES_PATH=data/cities.json
# DATA_USERS_PATH=data/users.json
# CORE_DEFAULT_TIMEZONE=null
# TELEGRAM_PERSISTENCE_PATH=null
```

**Important:** Do not commit `.env`; it is listed in `.gitignore`.

---

## Step 5: Configure configuration.yaml

`src/configuration.yaml` can use environment variables. You can:

1. **Leave as-is** — values come from `.env`
2. **Or override** specific values in YAML

**Environment variable syntax:**
- `${VAR_NAME}` — required (error if unset)
- `${VAR_NAME:default_value}` — optional with default

See `../config_schema.md` for the full schema.

---

## Step 6: Configure users.json

Edit `src/data/users.json` (or the path set in config):

```json
{
  "telegram:123456789": {
    "timezone": "Europe/Amsterdam"
  },
  "telegram:987654321": {
    "timezone": "Asia/Yerevan"
  },
  "channel:-1001234567890": {
    "default_timezone": "Europe/Amsterdam",
    "members": [
      "telegram:123456789",
      "telegram:987654321"
    ]
  }
}
```

**Notes:**
- Replace IDs with your real user and chat IDs
- Use IANA timezone IDs only (no offset strings like `+03:00` in users.json)
- `channel:-1001234567890` must match the group `chat_id` used by the bot
- See `../USER_PROFILE_MODEL.md` and `../data/users.example.json`

**Common IANA IDs:** `Europe/Amsterdam`, `America/New_York`, `Asia/Tokyo`, etc.  
Full list: [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

---

## Step 7: Install dependencies

From project root:

```bash
pip install -r src/requirements.txt
```

Or use a virtual environment: `python3 -m venv venv`, then `source venv/bin/activate` (Unix) and `pip install -r src/requirements.txt`. See `../DEPENDENCIES.md`.

---

## Step 8: Run the bot

From project root:

```bash
python src/main.py
```

Or from `src/`:

```bash
cd src
./run.sh
```

**Expected output on success:**
```
... - adapters.telegram.adapter - INFO - Starting Telegram adapter...
... - adapters.telegram.adapter - INFO - Adapter started and polling for updates
```

The bot is now listening in the configured chat.

---

## Step 9: Test behavior

### Test 1: Time with explicit timezone

Send in the group:
```
Meeting at 10:30 UTC+3
```

**Expected:** Bot replies with time in +03:00 and other timezones (if configured).

### Test 2: Time with city name

Send:
```
Call at 14:00 Amsterdam
```

**Expected:** Reply shows time in Europe/Amsterdam (and other timezones per config).

### Test 3: Time without explicit timezone (user profile)

If the sender has a timezone in `users.json`:
```
Meeting at 15:30
```

**Expected:** Time converted using user timezone and channel active timezones.

### Test 4: 12-hour format

```
Standup at 9:00am
```

**Expected:** Converted to 24h and shown in configured timezones.

### Test 5: Ambiguous time (no reply)

```
Call at 8
```

**Expected:** Bot does not reply (bare hour without AM/PM is ambiguous).

### Test 6: Message edit

1. Send: `Meeting at 10:00`
2. Edit to: `Meeting at 11:00`

**Expected:** Previous reply is deleted; new reply is sent.

More examples: see `TEST_PHRASES.md`.

---

## Step 10: Logging

Log level can be set in `configuration.yaml`:

```yaml
logging:
  level: "DEBUG"   # DEBUG, INFO, WARNING, ERROR
```

Use DEBUG for troubleshooting (e.g. which timezone was resolved, which time was detected).

---

## Troubleshooting

### "telegram.token is required" or TELEGRAM_TOKEN not set

- Ensure `.env` exists in project root (or as configured)
- Ensure `TELEGRAM_TOKEN=your_token` is in `.env`
- If using env vars from config, ensure `python-dotenv` is installed: `pip install python-dotenv`

### "Cities file not found"

- Ensure `src/data/cities.json` exists (or path in config is correct)
- Config typically uses `data/cities.json` relative to the config file location

### Bot does not reply in the group

- Ensure the bot is added to the group
- Ensure `chat_id` in config matches the group ID (negative for groups)
- Check logs for errors
- Ensure the message contains a supported time format (see `../spec/TIME_PARSING_RULES.md`)

### "Invalid timezone"

- Use only IANA timezone IDs in `users.json` (e.g. `Europe/Amsterdam`), not offset strings like `+03:00`
- Check IDs against [tz database list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- See `../USER_PROFILE_MODEL.md` §9

---

## Optional config (configuration.yaml)

**Max timezones in reply:**
```yaml
output:
  max_timezones: 5   # 1–10
```

**Ordering:**
```yaml
output:
  ordering: "SOURCE_FIRST"   # SOURCE_FIRST, OFFSET_ASC, ALPHABETICAL
```

**Max time mentions per message:**
```yaml
core:
  max_time_mentions: 3   # 1–10
```

---

## Stopping the bot

Press `Ctrl+C` in the terminal.

---

## References

- `RUNNING.md` — core vs full application
- `src/README.md` — Quick Start
- `../config_schema.md` — configuration schema
- `../USER_PROFILE_MODEL.md` — users.json and profiles
- `TEST_PHRASES.md` — test message examples

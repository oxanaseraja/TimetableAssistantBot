# DEPENDENCIES.md — MVP Runtime Stack

This document defines the exact runtime dependencies for MVP.
LLM must use **only** these libraries — no alternatives, no additions.

---

## 1. Python Version

```
Python >= 3.10
```

**Why 3.10+:**
- `zoneinfo` is stdlib (no pytz needed)
- Better type hints
- Pattern matching (optional, nice to have)

---

## 2. Core Dependencies

Core uses **standard library only**:

| Module | Purpose |
|--------|---------|
| `datetime` | Time manipulation |
| `zoneinfo` | Timezone conversion (IANA database) |
| `re` | Regex-based time parsing |
| `hashlib` | SHA256 for ID mapping |
| `json` | Loading cities.json, users.json |

**No external dependencies in core.**

---

## 3. Adapter Dependencies

### Telegram Adapter

```
python-telegram-bot >= 20.0, < 21.0
```

**Why python-telegram-bot:**
- De facto standard for Python Telegram bots
- Async-first in v20+
- Good type hints
- Active maintenance

**API style:** Use `python-telegram-bot` v20+ async API:

```python
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

async def handle_message(update: Update, context):
    # process message
    pass

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
```

---

### Configuration

```
pyyaml >= 6.0
```

**Why pyyaml:**
- Standard YAML parser
- Used for `configuration.yaml`

---

## 4. Forbidden Dependencies (MVP)

These are explicitly **NOT allowed**:

| Library | Reason |
|---------|--------|
| `pytz` | Use `zoneinfo` instead |
| `dateutil` | Overkill for MVP parsing |
| `arrow` | Unnecessary abstraction |
| `pendulum` | Unnecessary abstraction |
| `spacy`, `nltk` | No NLP in MVP |
| `openai`, `anthropic` | No LLM-based parsing |

---

## 5. requirements.txt

```
python-telegram-bot>=20.0,<21.0
pyyaml>=6.0
```

---

## 6. Development Dependencies (Optional)

For testing and development:

```
pytest>=7.0
pytest-asyncio>=0.21.0
```

These are **not required** for runtime.

---

## 7. Installation

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 8. Timezone Database

`zoneinfo` uses system IANA timezone database.

**On Linux:** Usually pre-installed (`/usr/share/zoneinfo`)
**On macOS:** Pre-installed
**On Windows:** Install `tzdata` package:

```
pip install tzdata
```

Add to requirements.txt for Windows compatibility:
```
tzdata; sys_platform == "win32"
```

---

## 9. References

- `POLICIES.md` — Core rules (stdlib only)
- `TELEGRAM_ADAPTER.md` — Adapter implementation plan
- `configuration.yaml` — Runtime configuration

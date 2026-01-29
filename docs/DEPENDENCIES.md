# DEPENDENCIES.md — MVP Runtime Stack

This document defines the exact runtime dependencies for MVP.
LLM must use **only** these libraries — no alternatives, no additions.

---

## 1. Python Version

```
Python >= 3.9
```

**Why 3.9+:** `zoneinfo` is stdlib (no pytz needed).

---

## 2. Core Dependencies

Core (`src/core/`) uses **standard library only**:

| Module | Purpose |
|--------|---------|
| `datetime` | Time manipulation |
| `zoneinfo` | Timezone conversion (IANA database) |
| `re` | Regex-based time parsing |
| `typing`, `dataclasses` | Type hints and DTOs |
| `logging` | Debug/info (allowed per CORE_CONTRACT) |

Adapter modules (e.g. `event_mapping`, `user_loader`) also use stdlib: `hashlib` (SHA256 for ID mapping), `json` (loading cities.json, users.json). Core never loads files; adapter passes data in.

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

### Environment Variables

```
python-dotenv >= 1.0.0
```

**Why python-dotenv:**
- Load `.env` files for local development
- Keeps secrets out of repo while supporting easy setup

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
# Telegram Bot API
python-telegram-bot>=20.0,<21.0

# Configuration parsing
pyyaml>=6.0

# Environment variable loading (.env file support)
python-dotenv>=1.0.0

# Windows timezone support (optional, auto-installed on Windows)
tzdata; sys_platform == "win32"
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
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies (requirements.txt is in src/)
pip install -r src/requirements.txt
```

---

## 8. Timezone Database

`zoneinfo` uses system IANA timezone database.

**On Linux:** Usually pre-installed (`/usr/share/zoneinfo`)
**On macOS:** Pre-installed
**On Windows:** The project's `requirements.txt` already includes `tzdata; sys_platform == "win32"` so `pip install -r requirements.txt` installs `tzdata` on Windows. Without it, `zoneinfo` may fail on Windows.

---

## 9. References

- `POLICIES.md` — Core rules (stdlib only)
- `TELEGRAM_ADAPTER.md` — Adapter implementation plan
- `CORE_CONTRACT.md` — Core invocation (logging allowed in core)
- `configuration.yaml` — Runtime configuration (in `src/`)

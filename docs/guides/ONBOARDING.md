# Onboarding

This repository contains a minimal, platform-agnostic core for time parsing and
timezone conversion. MVP platform: Telegram.
Discord/WhatsApp adapters are Optional / Future.

Start here:
- `../spec/ARCHITECTURE.md` for the minimal architecture summary.
- `../spec/POLICIES.md` for deterministic rules (MVP).
- `../spec/CONTRACTS.md` for DTO contracts (MVP).
- `../spec/CORE_CONTRACT.md` for core invocation contract.
- `../STATE_MODEL.md` for state ownership (MVP).
- `../TESTING_STRATEGY.md` for test architecture (MVP).

For full document index and reading order see `../DOC_INDEX.md`.

**Running and testing locally:** See `LOCAL_TESTING.md` for step-by-step setup (token, chat_id, users.json, run). See `TEST_PHRASES.md` for example messages to try.

Core modules:
- `core/parser/` — time parsing
- `core/timezone/` — timezone conversion utilities

**Why these constraints (rationale):** Regex-only (deterministic, no LLM). Ambiguity → no reply (no guesswork). Telegram MVP (fast validation). SHA256 IDs (reproducible). Cap timezones/time mentions (scannable, bounded). Local cities (no external API). No dialogs (adapter sends nothing on `None`). Rules: `../spec/POLICIES.md`, `../spec/CONTRACTS.md`, `../spec/CORE_CONTRACT.md`.

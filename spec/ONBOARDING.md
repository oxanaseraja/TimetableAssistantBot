# Onboarding

This repository contains a minimal, platform-agnostic core for time parsing and
timezone conversion. MVP platform: Telegram.
Discord/WhatsApp adapters are Optional / Future.

Start here:
- `ARCHMINI.md` for the minimal architecture summary.
- `POLICIES.md` for deterministic rules (MVP).
- `CONTRACTS.md` for DTO contracts (MVP).
- `CORE_CONTRACT.md` for core invocation contract.
- `STATE_MODEL.md` for state ownership (MVP).
- `TESTING_STRATEGY.md` for test architecture (MVP).

Core modules:
- `core/parser/` — time parsing
- `core/timezone/` — timezone conversion utilities

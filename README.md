# TimetableAssistantBot

A Discord/Telegram/WhatsApp bot that monitors a channel and automatically converts mentioned times into multiple timezones.

## Project Structure

```
TimetableAssistantBot/
├── docs/                    # Documentation (specification, onboarding, runbook)
│   ├── DOC_INDEX.md         # Start here - document index
│   ├── ARCHITECTURAL_INVARIANTS.md
│   ├── TIME_PARSING_RULES.md
│   ├── TIMEZONE_EXTRACTION_RULES.md
│   ├── POLICIES.md
│   ├── CONTRACTS.md
│   ├── ...
│   └── data/                # Example data files
│
├── src/                     # Source code (implementation)
│   ├── core/                # Platform-agnostic core
│   ├── adapters/            # Platform-specific adapters
│   ├── data/                # Runtime data files
│   ├── requirements.txt
│   ├── configuration.yaml
│   └── run.sh
│
└── README.md                # This file
```

## Quick Start

### For LLM Code Generator

1. Read `docs/DOC_INDEX.md` for document reading order
2. Read `docs/ARCHITECTURAL_INVARIANTS.md` for system constraints
3. Implement code in `src/` following the specification

### For Developers

1. Read `docs/ONBOARDING.md` for project overview
2. See `docs/DEPENDENCIES.md` for runtime requirements
3. Copy `src/env.example` to `src/.env` and configure
4. Run `pip install -r src/requirements.txt`
5. Run `src/run.sh`

## MVP Platform

Telegram is the MVP platform. Discord/WhatsApp are future scope.

## Key Documents

| Document | Purpose |
|----------|---------|
| `docs/ARCHITECTURAL_INVARIANTS.md` | System constraints (must-read) |
| `docs/TIME_PARSING_RULES.md` | Time parsing grammar |
| `docs/POLICIES.md` | Behavioral rules |
| `docs/END_TO_END_FLOW.md` | Step-by-step example |
| `docs/SPEC_FREEZE.md` | Specification freeze (v1.0) |

## Specification Status

The MVP specification is formally frozen in `docs/SPEC_FREEZE.md`.

All behavioral contracts, invariants, limits and scope boundaries are fixed there.
Further changes require a new spec version.




Как использовать
Для LLM-кодогенератора:
Прочитать docs/DOC_INDEX.md — порядок чтения документов
Начать с docs/ARCHITECTURAL_INVARIANTS.md
Реализовать код в src/ по спецификации
Для разработчика:
Прочитать docs/README.md
Реализовать модули в src/core/ и src/adapters/
Запустить src/run.sh
Документация полностью отделена от кода. LLM читает docs/, пишет в src/.

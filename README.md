# TimetableAssistantBot

A Discord/Telegram/WhatsApp bot that monitors a channel and automatically converts mentioned times into multiple timezones.

## Project Structure

```
TimetableAssistantBot/
├── spec/                    # Specification (for LLM to read)
│   ├── DOC_INDEX.md         # Start here - document index
│   ├── ARCHITECTURAL_INVARIANTS.md
│   ├── TIME_PARSING_RULES.md
│   ├── TIMEZONE_EXTRACTION_RULES.md
│   ├── POLICIES.md
│   ├── CONTRACTS.md
│   ├── ...
│   └── data/                # Example data files
│
├── bot/                     # Implementation (written by LLM)
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

1. Read `spec/DOC_INDEX.md` for document reading order
2. Read `spec/ARCHITECTURAL_INVARIANTS.md` for system constraints
3. Implement code in `bot/` following the specification

### For Developers

1. Read `spec/ONBOARDING.md` for project overview
2. See `spec/DEPENDENCIES.md` for runtime requirements
3. Copy `bot/env.example` to `bot/.env` and configure
4. Run `pip install -r bot/requirements.txt`
5. Run `bot/run.sh`

## MVP Platform

Telegram is the MVP platform. Discord/WhatsApp are future scope.

## Key Documents

| Document | Purpose |
|----------|---------|
| `spec/ARCHITECTURAL_INVARIANTS.md` | System constraints (must-read) |
| `spec/TIME_PARSING_RULES.md` | Time parsing grammar |
| `spec/POLICIES.md` | Behavioral rules |
| `spec/END_TO_END_FLOW.md` | Step-by-step example |







Как использовать
Для LLM-кодогенератора:
Прочитать spec/DOC_INDEX.md — порядок чтения документов
Начать с spec/ARCHITECTURAL_INVARIANTS.md
Реализовать код в bot/ по спецификации
Для разработчика:
Прочитать spec/README.md
Реализовать модули в bot/core/ и bot/adapters/
Запустить bot/run.sh
Спецификация полностью отделена от кода. LLM читает spec/, пишет в bot/.

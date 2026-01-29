# TimetableAssistantBot

A Discord/Telegram/WhatsApp bot that monitors a channel and automatically converts mentioned times into multiple timezones.

## Project Structure

```
TimetableAssistantBot/
├── docs/                    # Documentation (specification, onboarding, runbook)
│   ├── DOC_INDEX.md         # Start here - document index
│   ├── spec/                # Frozen specification (architecture, contracts, grammar)
│   ├── guides/              # Onboarding, local testing, developer guide
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
2. Read `docs/spec/ARCHITECTURAL_INVARIANTS.md` for system constraints
3. Implement code in `src/` following the specification

### For Developers

1. Read `docs/guides/ONBOARDING.md` for project overview
2. See `docs/DEPENDENCIES.md` for runtime requirements
3. Copy `src/env.example` to `src/.env` and configure
4. Run `pip install -r src/requirements.txt`
5. Run `src/run.sh`

## MVP Platform

Telegram is the MVP platform. Discord/WhatsApp are future scope.

## Key Documents

| Document | Purpose |
|----------|---------|
| `docs/spec/ARCHITECTURAL_INVARIANTS.md` | System constraints (must-read) |
| `docs/spec/TIME_PARSING_RULES.md` | Time parsing grammar |
| `docs/spec/POLICIES.md` | Behavioral rules |
| `docs/END_TO_END_FLOW.md` | Step-by-step example |
| `docs/spec/SPEC_FREEZE.md` | Specification freeze (v1.0) |

## Specification Status

The MVP specification is formally frozen in `docs/spec/SPEC_FREEZE.md`.

All behavioral contracts, invariants, limits and scope boundaries are fixed there.
Further changes require a new spec version.

## How to Use

**For LLM code generator:**
- Read `docs/DOC_INDEX.md` for document reading order
- Start with `docs/spec/ARCHITECTURAL_INVARIANTS.md`
- Implement code in `src/` according to the specification

**For developers:**
- Read `docs/README.md`
- Implement modules in `src/core/` and `src/adapters/`
- Run `src/run.sh`

Documentation is fully separate from code. LLM reads `docs/`, writes to `src/`.

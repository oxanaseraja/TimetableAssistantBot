# Spec Coverage Map

This document tracks which specification documents are implemented and where.

**Update this file when implementing a docs document.**

---

## Implementation Status

| Spec Document | Status | Implemented In |
|---------------|--------|----------------|
| `CONTRACTS.md` | ⬜ TODO | `core/contracts.py` |
| `TIME_PARSING_RULES.md` | ⬜ TODO | `core/parser/time_parser.py` |
| `TIMEZONE_EXTRACTION_RULES.md` | ⬜ TODO | `core/timezone/extractor.py` |
| `POLICIES.md` | ⬜ TODO | `core/processor.py` |
| `CORE_CONTRACT.md` | ⬜ TODO | `core/processor.py` |
| `USER_PROFILE_MODEL.md` | ⬜ TODO | `adapters/telegram/user_loader.py` |
| `ADAPTER_CONTRACTS.md` | ⬜ TODO | `adapters/telegram/adapter.py` |
| `TELEGRAM_ADAPTER.md` | ⬜ TODO | `adapters/telegram/` |
| `DEPENDENCIES.md` | ✅ DONE | `requirements.txt` |

---

## Status Legend

- ⬜ TODO — not started
- 🔄 WIP — work in progress
- ✅ DONE — implemented and tested
- ⚠️ PARTIAL — partially implemented

---

## Module → Spec Mapping

| Module | Implements Spec |
|--------|-----------------|
| `core/contracts.py` | `CONTRACTS.md` |
| `core/parser/time_parser.py` | `TIME_PARSING_RULES.md` |
| `core/timezone/extractor.py` | `TIMEZONE_EXTRACTION_RULES.md` |
| `core/timezone/converter.py` | `POLICIES.md` §conversion |
| `core/processor.py` | `CORE_CONTRACT.md`, `POLICIES.md` |
| `adapters/telegram/adapter.py` | `ADAPTER_CONTRACTS.md`, `TELEGRAM_ADAPTER.md` |
| `adapters/telegram/event_mapping.py` | `POLICIES.md` §8 (ID mapping) |
| `adapters/telegram/formatter.py` | `ADAPTER_CONTRACTS.md` §6 (output format) |
| `adapters/telegram/user_loader.py` | `USER_PROFILE_MODEL.md` |

---

## Notes

- Each module docstring should reference its source docs
- Tests should reference `docs/END_TO_END_FLOW.md` for golden cases
- If a docs document is missing implementation → flag as TODO

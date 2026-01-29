# DOC_INDEX.md — Specification Document Index

This is the entry point for the specification.
All documents are in this `docs/` folder.

---

## Reading Order for LLM

0. `LLM_EXECUTION_PROTOCOL.md` — **execution rules (read first)**
1. `IMPLEMENTATION_CONSTRAINTS.md` — **hard rules (must follow)**
2. `spec/SPEC_FREEZE.md` — **frozen behavioral specification (MVP v1.0.0)**
3. `spec/ARCHITECTURAL_INVARIANTS.md` — system invariants
4. `spec/ARCHITECTURE.md` — system overview
5. `spec/TIME_PARSING_RULES.md` — input contract (time)
6. `spec/TIMEZONE_EXTRACTION_RULES.md` — input contract (timezone)
7. `spec/POLICIES.md` — behavioral rules
8. `spec/CONTRACTS.md` — DTO definitions
9. `END_TO_END_FLOW.md` — step-by-step example
10. `USER_PROFILE_MODEL.md` — data source
11. `DEPENDENCIES.md` — runtime stack
12. `ADAPTER_CONTRACTS.md` — adapter behavior
13. `TELEGRAM_ADAPTER.md` — Telegram implementation plan

---

## Document Categories

### Getting Started
- `guides/ONBOARDING.md` — quick start guide for new developers
- `guides/LOCAL_TESTING.md` — step-by-step local setup and testing (token, chat_id, users.json, run)
- `README.md` — spec folder overview

### System Constraints
- `spec/ARCHITECTURAL_INVARIANTS.md` — 23 invariants (must-read)
- `spec/ARCHITECTURE.md` — system overview and boundaries
- `spec/SPEC_FREEZE.md` — frozen behavioral specification (MVP v1.0.0)

### Input Contracts (Grammar)
- `spec/TIME_PARSING_RULES.md` — regex patterns for time parsing
- `spec/TIMEZONE_EXTRACTION_RULES.md` — timezone hint matching

### Behavioral Rules
- `spec/POLICIES.md` — core policies
Design rationale: see `guides/ONBOARDING.md` (Why these constraints)
- Converter rules (utc_offset format, partial failure): see `spec/CORE_CONTRACT.md` §UTC Offset Formatting, §Partial Failure

### Data Contracts
- `spec/CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — user data source
- `STATE_MODEL.md` — state ownership
- `STORAGE_MODEL.md` — MVP vs production storage

### Runtime Contracts
- `ADAPTER_CONTRACTS.md` — adapter runtime contract
- `TELEGRAM_ADAPTER.md` — Telegram implementation plan
- `spec/CORE_CONTRACT.md` — core invocation interface
- `DEPENDENCIES.md` — Python version, libraries
- `config_schema.md` — configuration YAML schema
- `guides/RUNNING.md` — core execution instructions

### Examples
- `END_TO_END_FLOW.md` — complete walkthrough with DTOs
- `guides/TEST_PHRASES.md` — example messages for manual testing
- `data/cities.json` — city whitelist example
- `data/users.example.json` — user config example

### Quality & Process
- `TESTING_STRATEGY.md` — test architecture
- `ARCH_CHECKLIST.md` — completeness checklist
- `ARCH_DIAGRAM.md` — architecture diagram
- `guides/DEVELOPER_GUIDE.md` — practical guidelines for developers

### Execution Protocol
- `LLM_EXECUTION_PROTOCOL.md` — rules for LLM code generation
- `IMPLEMENTATION_CONSTRAINTS.md` — hard constraints for implementation
- `HANDOVER.md` — specification gap handling and AI verification notes

### Project Management
- `TASK.md` — task definition
- `FUTURE_WORK.md` — planned future enhancements
- `limitationsOfReality.md` — known limitations and constraints
- `PROJECT_ANALYSIS.md` — project analysis

### Meta
- `DOC_INDEX.md` — this file
- `LLM_SPEC_ANALYSIS.md` — specification readiness analysis
- `journal/PROGRESS.md` — implementation journal
- `journal/01_spec_architecture.md` — architecture specification journal entry

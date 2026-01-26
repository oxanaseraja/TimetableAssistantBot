# DOC_INDEX.md — Specification Document Index

This is the entry point for the specification.
All documents are in this `docs/` folder.

---

## Reading Order for LLM

0. `LLM_EXECUTION_PROTOCOL.md` — **execution rules (read first)**
1. `IMPLEMENTATION_CONSTRAINTS.md` — **hard rules (must follow)**
2. `ARCHITECTURAL_INVARIANTS.md` — system invariants
3. `ARCHMINI.md` — system overview
3. `TIME_PARSING_RULES.md` — input contract (time)
4. `TIMEZONE_EXTRACTION_RULES.md` — input contract (timezone)
5. `POLICIES.md` — behavioral rules
6. `CONTRACTS.md` — DTO definitions
7. `END_TO_END_FLOW.md` — step-by-step example
8. `USER_PROFILE_MODEL.md` — data source
9. `DEPENDENCIES.md` — runtime stack
10. `ADAPTER_CONTRACTS.md` — adapter behavior
11. `TELEGRAM_ADAPTER.md` — Telegram implementation plan

---

## Document Categories

### System Constraints
- `ARCHITECTURAL_INVARIANTS.md` — 16 invariants (must-read)
- `ARCHMINI.md` — system overview and boundaries

### Input Contracts (Grammar)
- `TIME_PARSING_RULES.md` — regex patterns for time parsing
- `TIMEZONE_EXTRACTION_RULES.md` — timezone hint matching

### Behavioral Rules
- `POLICIES.md` — core policies
- `DESIGN_CHOICES.md` — design rationale

### Data Contracts
- `CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — user data source
- `STATE_MODEL.md` — state ownership
- `STORAGE_MODEL.md` — MVP vs production storage

### Runtime Contracts
- `ADAPTER_CONTRACTS.md` — adapter runtime contract
- `TELEGRAM_ADAPTER.md` — Telegram implementation plan
- `CORE_CONTRACT.md` — core invocation interface
- `DEPENDENCIES.md` — Python version, libraries

### Examples
- `END_TO_END_FLOW.md` — complete walkthrough with DTOs
- `data/cities.json` — city whitelist example
- `data/users.example.json` — user config example

### Quality & Process
- `TESTING_STRATEGY.md` — test architecture
- `ARCH_CHECKLIST.md` — completeness checklist
- `ARCH_DIAGRAM.md` — architecture diagram

### Execution Protocol
- `LLM_EXECUTION_PROTOCOL.md` — rules for LLM code generation
- `IMPLEMENTATION_CONSTRAINTS.md` — hard constraints for implementation

### Meta
- `DOC_INDEX.md` — this file
- `README.md` — spec folder overview
- `LLM_SPEC_ANALYSIS.md` — specification readiness analysis
- `journal/PROGRESS.md` — implementation journal

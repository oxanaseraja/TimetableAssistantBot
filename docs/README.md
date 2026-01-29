# Specification

This folder contains the complete specification for the TimetableAssistantBot.

**Purpose:** LLM reads these documents to generate implementation code in `../src/`.

---

## ⚠️ Read-Only Directory

**Spec directory is immutable during implementation.**

- Implementation must not modify any file in `docs/`
- All changes to spec are architectural decisions, not implementation fixes
- If spec is incomplete → stop and report missing contract
- See `LLM_EXECUTION_PROTOCOL.md` for execution rules

---

## Reading Order

### 1. System Constraints (Must-Read First)

- `spec/ARCHITECTURAL_INVARIANTS.md` — 23 invariants that must always hold

### 2. Input Contracts (Grammar)

- `spec/TIME_PARSING_RULES.md` — regex patterns for time parsing
- `spec/TIMEZONE_EXTRACTION_RULES.md` — timezone hint matching rules

### 3. Behavioral Rules

- `spec/POLICIES.md` — core policies (references grammar files)
- `guides/ONBOARDING.md` — rationale (Why these constraints)

### 4. Data Contracts

- `spec/CONTRACTS.md` — DTO definitions
- `USER_PROFILE_MODEL.md` — user data source

### 5. Runtime Contracts

- `ADAPTER_CONTRACTS.md` — adapter behavior
- `TELEGRAM_ADAPTER.md` — Telegram-specific implementation plan
- `spec/CORE_CONTRACT.md` — core invocation interface

### 6. Examples

- `END_TO_END_FLOW.md` — step-by-step walkthrough with DTOs

### 7. Dependencies

- `DEPENDENCIES.md` — Python version, libraries, constraints

---

## Document Index

See `DOC_INDEX.md` for the complete list of documents.

---

## Data Files

The `data/` folder contains example data files:

- `cities.json` — city-to-timezone whitelist
- `users.example.json` — example user/channel configuration

These should be copied to `../src/data/` and customized for runtime.

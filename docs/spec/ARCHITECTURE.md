# ARCHITECTURE.md — System Architecture (Platform‑Agnostic Core)

## 1. Goal & Scope

**Primary Goal:** Automatically find time mentions in messages and show that time in the active timezones of channel participants.

**MVP Scope:**
- Platform-agnostic core with deterministic logic
- First adapter: Telegram only
- Discord/WhatsApp — optional future extensions
- Time parsing via regex patterns only (no LLM interpretation)

**Boundary Rule:** Core never sees platform identifiers. All platform identity is resolved at adapter boundary.

---

## 2. Architectural Overview

### 2.1. High-Level Diagram
┌───────────────────────────────┐
│ ADAPTERS │
│ Telegram (MVP) │
│ Discord / WhatsApp (Future) │
└──────────────┬────────────────┘
│ CoreMessageEvent + context
│ (5 arguments total, see §3.1)
▼
┌───────────────────────────────┐
│ CORE │
│ Parsing → Context → Resolve │
│ → Convert → DisplayBlock │
└──────────────┬────────────────┘
│ DisplayBlock | None
▼
┌───────────────────────────────┐
│ ADAPTER OUTPUT │
│ Format + Send reply │
│ (send nothing when None) │
└───────────────────────────────┘


**Key Notes:**
- Core receives five arguments from adapter (see `CORE_CONTRACT.md`)
- When core returns `None`, adapter sends nothing (no reply)
- All time parsing uses regex only (no external APIs or LLMs)

### 2.2. Core Pipeline (Detailed Flow)

1. **Input**: `CoreMessageEvent` (text + internal IDs, timestamp_utc)
2. **Parsing**: Extract `DetectedTime` and timezone hints via regex (see `TIME_PARSING_RULES.md`)
3. **Context**: Obtain `UserProfile` and `ChannelContext` from provided data
4. **Interpretation**: Resolve time to `ResolvedTimeContext` using deterministic rules (`POLICIES.md`)
5. **Conversion**: Convert to all active timezones in channel
6. **Output**: Generate `DisplayBlock` (semantic output; formatting is adapter responsibility)

**Pipeline Execution Rules:**
- Stage order is fixed: Parsing → Context → Interpretation → Conversion → Output
- Stop reasons (return `None`): no time detected, ambiguity, user suppression
- Core never raises exceptions to adapters
- All stages are pure logic (no I/O, no side effects)

---

## 3. Component Dependencies

### 3.1. Adapters Depend On:
- `ADAPTER_CONTRACTS.md` — runtime requirements and lifecycle
- `CONTRACTS.md` — DTO definitions for data exchange
- `CORE_CONTRACT.md` — core invocation interface
- Platform-specific specifications (e.g., `TELEGRAM_ADAPTER.md`)

### 3.2. Core Depends On:
- `POLICIES.md` — deterministic behavioral rules
- `TIME_PARSING_RULES.md` — regex patterns for time detection
- `TIMEZONE_EXTRACTION_RULES.md` — rules for timezone hint matching
- `CONTRACTS.md` — internal DTO definitions

---

## 4. Repository Structure
project/
├── src/
│   ├── core/           # Platform-agnostic core logic
│   ├── adapters/       # Platform-specific implementations
│   │   └── telegram/   # MVP adapter
│   ├── configuration.yaml
│   ├── env.example
│   ├── run.sh
│   ├── main.py
│   └── data/           # cities.json, users.json (paths from config)
├── docs/
│   ├── journal/        # Implementation specs
│   └── [architecture documents]
└── tests/


---

## 5. Extension Points & Evolution

### 5.1. Adding New Platforms
- Create new adapter under `src/adapters/` (e.g., `src/adapters/discord/`)
- Implement `ADAPTER_CONTRACTS.md` requirements
- Update configuration as needed

### 5.2. Storage Evolution (Production)
- Current: In-memory state (MVP)
- Future: Persistent storage layer (see `STORAGE_MODEL.md`, `STATE_MODEL.md`)

### 5.3. Rule Extensions
- Modify parser rules via `TIME_PARSING_RULES.md`
- Update behavioral policies in `POLICIES.md`
- All changes require spec updates first

---

## 6. Key References

| Document | Purpose |
|----------|---------|
| `POLICIES.md` | Deterministic behavioral rules |
| `CONTRACTS.md` | Data transfer object definitions |
| `CORE_CONTRACT.md` | Core invocation interface |
| `ADAPTER_CONTRACTS.md` | Adapter runtime requirements |
| `TIME_PARSING_RULES.md` | Regex patterns for time parsing |
| `ONBOARDING.md` | Rationale (Why these constraints) |
| `TESTING_STRATEGY.md` | Testing approach and coverage |
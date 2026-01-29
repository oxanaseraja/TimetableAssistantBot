# ARCH_CHECKLIST.md — Architecture Completeness Checklist

This checklist captures the architecture topics that must be covered for a
complete, implementation-ready design. The referenced documents define the current MVP state.

---

## 1. Core Implementation Contract
MVP: required
- Define core processor interface (module, function signature).
- Specify sync vs async invocation.
- Define error behavior (no exceptions to adapter).
- Define return semantics (DisplayBlock | None and meaning of None).
See: `spec/CORE_CONTRACT.md`.

## 2. Pipeline Execution Spec
MVP: defined minimal
- Formalize stage order and branching.
- Define stop conditions and reasons (no time, ambiguity, suppression).
- Specify data passed between stages explicitly.
- Define side-effect policy (pure functions only, no I/O inside stages).
See: `spec/ARCHITECTURE.md`.

## 3. Data Ownership & Storage Architecture
MVP: defined minimal
- Define ownership of UserProfile/ChannelContext.
- Storage strategy (in-memory vs persistent).
- Retention and lifecycle rules (MVP: in-memory only, process lifetime).
See: `STATE_MODEL.md`.

## 4. Timezone & City Data Sources
MVP: defined
- Source of IANA timezones: `zoneinfo` (stdlib).
- City resolution: cities from `cities.json`; extraction per `TIMEZONE_EXTRACTION_RULES.md`; adapter populates cities in output (max 3 per timezone).
- Update policy: out of scope (static file in MVP).
See: `spec/POLICIES.md` §2, `spec/TIMEZONE_EXTRACTION_RULES.md`, `spec/CONTRACTS.md` (DisplayBlock), `ADAPTER_CONTRACTS.md` §6.

## 5. Security & Secrets
MVP: defined minimal
- Token storage strategy and access control.
- Behavior on missing/invalid credentials (fail fast, no retries).
- Rotation policy and environment separation.
See: `ADAPTER_CONTRACTS.md`.

## 6. Observability & Ops
MVP: defined minimal
- Logging levels and structure.
- Metrics to collect (errors, drops).
- Runbook and alerting: out of scope.
See: `ADAPTER_CONTRACTS.md`.

## 7. Testing Architecture
MVP: defined minimal
- Unit/integration/contract test scope.
- Golden cases aligned with `spec/POLICIES.md`.
- Deterministic inputs and frozen time.
- Coverage goals and CI: minimal in MVP (see `TESTING_STRATEGY.md`).
See: `TESTING_STRATEGY.md`, `END_TO_END_FLOW.md` (golden cases).

## 8. Deployment Architecture
MVP: defined minimal
- Telegram adapter mode (long-polling vs webhook).
- Runtime environment assumptions.
- Scaling and restart strategy.
- Platform constraints (Telegram Bot API limitations).
See: `TELEGRAM_ADAPTER.md`, `ADAPTER_CONTRACTS.md`.
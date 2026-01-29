# TESTING_STRATEGY.md — MVP Tests

Scope is minimal and deterministic. All tests are deterministic (fixed time, no network); see `IMPLEMENTATION_CONSTRAINTS.md` § Verification.

---

## 1. Core Unit Tests
- Time detection rules (POLICIES.md)
- Timezone precedence rules
- Ambiguity (safe-only)

## 2. Policy Golden Cases
- Canonical examples aligned to POLICIES.md
- Each case: input → expected DisplayBlock or None
- See `END_TO_END_FLOW.md` for step-by-step example used in processor tests

## 3. Adapter Contract Tests
- CoreMessageEvent mapping
- Duplicate suppression by internal_message_id
- Formatting rules (24h, HH:MM, timezone id)

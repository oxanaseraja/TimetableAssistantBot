# LLM Execution Protocol

This document defines the execution rules for LLM code generation.

---

## Before Writing Any Code

1. Read `DOC_INDEX.md` fully
2. Read `ARCHITECTURAL_INVARIANTS.md` before any other document
3. Read all referenced specification documents

---

## During Implementation

4. Do not implement features not specified in `docs/`
5. Do not infer missing behavior — if unclear, stop
6. If specification is incomplete → **stop and report missing contract**
7. Write code only in `src/` directory
8. Never modify any file in `docs/`

---

## Code Constraints

9. Core must be pure and deterministic
10. Adapter is the only source of IO
11. All parsing is regex-based (no NLP, no heuristics)
12. All ambiguity leads to `None` (no guessing)

---

## Testing

13. Write tests for all implemented modules
14. Tests must be deterministic (no real time, no network)
15. Use golden test cases from `END_TO_END_FLOW.md`

---

## Traceability

16. Update `src/SPEC_COVERAGE.md` when implementing a spec document
17. Each module should reference its source spec in docstring

---

## If In Doubt

**Stop. Do not guess. Report the gap.**

Missing spec = architectural decision needed, not implementation choice.

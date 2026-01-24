# IMPLEMENTATION_CONSTRAINTS.md — Hard Rules for LLM

These constraints are **absolute**. Violation = incorrect implementation.

---

## Core Constraints

1. **Core must be pure** — no global state, no IO, no storage access
2. **Core is a single function** — `process(event, user_profile, channel_context)`
3. **All state is passed as arguments** — no singletons, no caches, no module-level variables
4. **No inference beyond specified rules** — if spec doesn't define it, don't implement it
5. **No fallback heuristics** — missing data = ambiguity = None

---

## Parsing Constraints

6. **Time parsing is regex only** — patterns from `TIME_PARSING_RULES.md`
7. **Timezone extraction is whitelist only** — cities from `cities.json`
8. **No normalization of input** — don't convert `10.30` to `10:30`
9. **No NLP, no LLM, no ML** — pure deterministic matching

---

## Library Constraints

10. **Use only specified libraries** — see `DEPENDENCIES.md`
11. **No pytz** — use `zoneinfo` (stdlib)
12. **No dateutil** — use `datetime` + `zoneinfo`
13. **No external NLP** — no spacy, nltk, or similar

---

## Adapter Constraints

14. **Adapter owns all IO** — file loading, network, logging
15. **Adapter constructs all context** — UserProfile, ChannelContext
16. **Adapter catches all exceptions** — core errors → log + silence
17. **Adapter never modifies core logic** — only transforms data

---

## Behavioral Constraints

18. **Silence is valid** — no reply is acceptable behavior
19. **No "smart" improvements** — implement exactly what spec says
20. **No undocumented features** — if it's not in spec, it doesn't exist

---

## If Spec is Unclear

**STOP. Do not guess.**

- Report the ambiguity
- Do not "fill in" missing details
- Missing spec = architectural decision needed

---

## Verification

Before submitting implementation:

1. Core has no imports of `os`, `io`, `pathlib`, `requests`, etc.
2. Core has no global variables
3. Core function signature matches `CORE_CONTRACT.md`
4. All regex patterns match `TIME_PARSING_RULES.md` exactly
5. Tests use frozen time, no real network

# DESIGN_CHOICES.md — MVP Decisions

## 1. Regex-only time parsing
**Decision:** Time is parsed by explicit regex patterns only, not by LLM or heuristics.  
**Rationale:** Deterministic, testable, no guesswork. LLM implements exact patterns from spec.  
**Trade-off:** Unsupported formats (`10.30`, `half past 10`) are silently ignored.

## 2. Safe-only ambiguity
**Decision:** No assumed or probabilistic answers.  
**Rationale:** Prevents ambiguous outputs and LLM guesswork.  
**Trade-off:** Fewer replies; users may get no response.

## 3. Telegram as MVP platform
**Decision:** Only Telegram adapter is in MVP.  
**Rationale:** Fastest to validate integration end-to-end.  
**Trade-off:** Multi-platform support deferred.

## 4. Deterministic ID mapping (SHA256)
**Decision:** Internal IDs are derived by SHA256 of stable inputs.  
**Rationale:** Reproducible and platform-agnostic mapping.  
**Trade-off:** Requires consistent mapping spec across adapters.

## 5. Max 5 timezones per reply
**Decision:** Cap output to 5 timezones.  
**Rationale:** Prevents long, noisy replies; keeps output scannable.  
**Trade-off:** Some timezones may be omitted.

## 6. Max 3 time mentions per message
**Decision:** Process only first 3 time mentions per message.  
**Rationale:** Avoids message spam and keeps compute bounded.  
**Trade-off:** Later mentions are ignored.

## 7. Cities list is local in MVP
**Decision:** Adapter uses a local city list and groups cities by timezone.  
**Rationale:** Keeps determinism without external dependencies.  
**Trade-off:** City list is static and must be maintained manually.

## 8. No dialogs in MVP
**Decision:** Ambiguity returns `None`; adapter sends no reply.  
**Rationale:** Avoids conversation state and UX flows.  
**Trade-off:** Less helpful in ambiguous cases.

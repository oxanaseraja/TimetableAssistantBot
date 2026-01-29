## Handling Specification Gaps & AI Verification

**Where to go next:** Full document list and reading order — `DOC_INDEX.md`. Quick start for developers — `guides/ONBOARDING.md`.

### Intent

**Source of Truth:** The original specification documents (`spec/CONTRACTS.md`, `spec/POLICIES.md`, `spec/CORE_CONTRACT.md`, `spec/TIME_PARSING_RULES.md`, `spec/TIMEZONE_EXTRACTION_RULES.md`) are the authoritative source. `spec/SPEC_FREEZE.md` and HANDOVER.md were added in a second iteration and must align with the original specification.

This project was implemented under an intentionally incomplete and evolving specification.
During development, multiple layers of formal contracts were introduced (CORE_CONTRACT, TIME_PARSING_RULES, TIMEZONE_EXTRACTION_RULES, SPEC_FREEZE, etc.) and iteratively aligned with the codebase.

The final **SPEC_FREEZE** document does not represent the initial product brief, but the result of a **convergence process** between:

* product intent
* architectural constraints
* UX invariants
* implementation feasibility
* systematic AI-assisted verification

AI tools (Cursor IDE, LLM code reviewers) were used not for generation only, but as **systematic static verifiers**:

* line-by-line comparison of code vs specification
* detection of contract violations
* detection of specification gaps and internal contradictions

All detected mismatches were classified and either:

* fixed in code,
* fixed in specification, or
* explicitly accepted as MVP constraints.

SPEC_FREEZE records the final converged behavioral snapshot of the MVP.

It is NOT an independent source of truth.

Authoritative sources remain:
- `spec/CONTRACTS.md` — data structures and DTO contracts  
- `spec/POLICIES.md` — behavioral rules and priority logic  
- `spec/CORE_CONTRACT.md` — core interface guarantees  

`spec/SPEC_FREEZE.md` documents the resolved interpretation of these contracts
after convergence and AI verification.

---

## Classification of AI-Detected Findings

All AI-reported mismatches were classified using the following decision table.
This classification governs whether an issue is fixed in code, fixed in specification, or explicitly frozen.

| Category                   | Description                                               | Action                                   | Rationale                                   |
| -------------------------- | --------------------------------------------------------- | ---------------------------------------- | ------------------------------------------- |
| **Spec contradiction**     | Two or more specification rules are mutually inconsistent | Update specification                     | Code must follow a single coherent contract |
| **Spec gap**               | Behavior exists in code but is undefined in specification | Update specification or remove behavior  | Prevent undocumented semantics              |
| **Code violation**         | Code contradicts an explicit frozen rule                  | Fix code                                 | Code must align with authoritative sources   |
| **MVP simplification**     | Behavior intentionally restricted vs full product intent  | Freeze behavior and document             | Prevent uncontrolled scope expansion        |
| **UX invariant**           | Behavior required to preserve UX predictability           | Preserve behavior, update spec if needed | UX stability has priority                   |
| **Out-of-scope extension** | Behavior beyond frozen MVP                                | Remove or document as future work        | Prevent scope creep                         |

Only mismatches in the first three categories were treated as **mandatory fixes**.
All MVP simplifications and UX invariants were intentionally frozen.

---

## Architectural Invariants

The following invariants define the core behavioral guarantees of the system.
They must be preserved by all future modifications.

### 1. Determinism

For identical inputs and identical context:

* parsing
* timezone resolution
* ordering
* formatting

must always produce identical outputs.

No randomization, implicit reordering, or environment-dependent behavior is permitted.

This is required for:

* reproducibility
* testability
* predictable UX

---

### 2. Silence Policy

The bot must remain silent unless:

* at least one valid time mention is detected
* a base timezone can be resolved
* at least one conversion result is produced

Invalid or ambiguous input must not generate partial or misleading output.
Excessive input is truncated and may produce partial output.

Failure modes are **silent by design**.

This prevents:

* noise in active chats
* misleading corrections
* user distrust

---

### 3. Resolution Priority

Timezone resolution follows a strictly ordered and deterministic priority chain.

Only explicitly documented sources may participate in resolution.
Implicit fallbacks are forbidden.

The priority order documented in POLICIES.md and frozen in SPEC_FREEZE must be treated as **architectural contract**.

Any change to resolution order is considered a **breaking behavioral change**.

---

### 4. UX Invariants

The following UX properties are considered contractual:

* Source timezone is always displayed first
* Output ordering is stable and predictable
* UTC is always rendered as `"UTC"`
* Partial results are explicitly marked
* Multiple independent time mentions are not silently merged

These invariants ensure:

* user trust
* interpretability
* low cognitive load

They have higher priority than implementation convenience.

---

## Representative Decision Examples

The following examples illustrate how specification gaps and AI findings were handled.

---

### Example 1 — Excess time mentions

**Finding:**
AI detected that messages with more than `max_time_mentions` were rejected entirely.

**Spec intent:**
Messages should be partially processed, not rejected.

**Decision:**

* Fix code to process first `max_time_mentions` (in MVP, only the first detected time is used)
* Do **not** set `partial=True` for time-mention overflow — `partial` is reserved for **timezone** truncation only (`max_timezones`); see `spec/SPEC_FREEZE.md` §3.1 and `spec/POLICIES.md`. Time-mention overflow is logged for diagnostics only.

**Rationale:**
Rejecting the entire message violates silence-policy and UX invariants.
Processing the first N mentions preserves utility while respecting limits.

---

### Example 2 — Multiple detected times, only first processed

**Finding:**
Code processes only the first detected time despite allowing multiple mentions.

**Spec status:**
SPEC_FREEZE does not require multi-time support in MVP.

**Decision:**

* Freeze behavior: process only the first time
* Explicitly document as MVP simplification

**Rationale:**
Multi-time output significantly complicates UX and formatting.
This is treated as an intentional MVP constraint, not a bug.

---

### Example 3 — Channel timezone priority vs offset ordering

**Finding:**
Channel default timezone was prioritized over strict UTC-offset sorting.

**Spec ambiguity:**
SPEC_FREEZE defined ordering by offset but did not specify channel behavior.

**Decision:**

* Preserve channel-priority behavior
* Update specification to document it

**Rationale:**
Channel default is a strong contextual signal.
Removing it would degrade UX in group contexts.

---

## Specification Authority Hierarchy

This project maintains a strict hierarchy of specification authority:

1. **`spec/CONTRACTS.md`**  
   Defines all DTO structures and data contracts.

2. **`spec/POLICIES.md`**  
   Defines behavioral rules, priority ordering, and decision policies.

3. **`spec/CORE_CONTRACT.md`**  
   Defines the core interface and processing guarantees.

4. **`spec/SPEC_FREEZE.md`**  
   Records the final converged behavioral snapshot of the MVP.
   It documents resolved interpretations but does not override the above sources.

5. **HANDOVER.md**  
   Describes process, rationale, and engineering decisions.

**Input contracts (also authoritative):** `spec/TIME_PARSING_RULES.md` and `spec/TIMEZONE_EXTRACTION_RULES.md` are part of the authoritative source (see Intent above). They are referenced by `spec/POLICIES.md` and `spec/CONTRACTS.md` as the grammar and extraction contracts; the hierarchy above lists the top-level structural documents.

**Rationale:**
SPEC_FREEZE is a convergence artifact, not a normative specification.
The authoritative sources remain the original architectural contracts.

---

## Notes for Future Development

* **Source of truth:** The original specification documents (`spec/CONTRACTS.md`, `spec/POLICIES.md`, `spec/CORE_CONTRACT.md`) are the authoritative source. `spec/SPEC_FREEZE.md` freezes the behavior derived from these documents.

* Any change affecting:

  * resolution priority
  * silence policy
  * ordering
  * partial semantics
    is considered a **breaking change** and must update SPEC_FREEZE

* AI verification is expected to be reused in future iterations using the same classification process

---

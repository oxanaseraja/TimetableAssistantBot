## Handling Specification Gaps & AI Verification

### Intent

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

The resulting SPEC_FREEZE defines the **authoritative behavioral contract** of the MVP.

---

## Classification of AI-Detected Findings

All AI-reported mismatches were classified using the following decision table.
This classification governs whether an issue is fixed in code, fixed in specification, or explicitly frozen.

| Category                   | Description                                               | Action                                   | Rationale                                   |
| -------------------------- | --------------------------------------------------------- | ---------------------------------------- | ------------------------------------------- |
| **Spec contradiction**     | Two or more specification rules are mutually inconsistent | Update specification                     | Code must follow a single coherent contract |
| **Spec gap**               | Behavior exists in code but is undefined in specification | Update specification or remove behavior  | Prevent undocumented semantics              |
| **Code violation**         | Code contradicts an explicit frozen rule                  | Fix code                                 | SPEC_FREEZE is authoritative                |
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

Invalid, ambiguous, or excessive input must not generate partial or misleading output.

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

The priority order frozen in SPEC_FREEZE must be treated as **architectural contract**.

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

* Fix code to process first `max_time_mentions`
* Set `partial=True` when overflow occurs

**Rationale:**
Rejecting the entire message violates silence-policy and UX invariants.
Partial output preserves utility while respecting limits.

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

## Notes for Future Development

* SPEC_FREEZE defines the only authoritative behavioral contract

* Any change affecting:

  * resolution priority
  * silence policy
  * ordering
  * partial semantics
    is considered a **breaking change** and must update SPEC_FREEZE

* AI verification is expected to be reused in future iterations using the same classification process

---

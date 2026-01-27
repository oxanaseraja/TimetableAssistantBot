# CONVERTER_RULES.md — Time Conversion Rules

This document clarifies converter behavior for edge cases
not fully described in `CORE_CONTRACT.md`.

---

## 1. UTC Offset Formatting

**Requirement:**
- The converter must return `utc_offset` strictly in `±HH:MM` format.
- If a valid offset cannot be produced, the timezone is skipped as invalid.

**Rationale:**
- No fallback values (e.g. `+00:00`) to avoid fabricating data.
- Preserves core determinism and data integrity.

**Algorithm:**
1. Get `offset = target_time.strftime("%z")`
2. If `offset` is empty or length is not 5, skip the timezone.
3. Otherwise compute `offset_formatted = f"{offset[:3]}:{offset[3:]}"`

---

## 2. Error Handling

- Any conversion error -> skip that timezone.
- Partial failures must not block successful conversions.


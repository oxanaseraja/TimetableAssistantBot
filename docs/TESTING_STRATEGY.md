# TESTING_STRATEGY.md — Testing Strategy (MVP)

## 1. Testing Philosophy

**Tests as Executable Specifications**  
Every test corresponds to a rule in `spec/POLICIES.md`, `spec/CONTRACTS.md`, `spec/CORE_CONTRACT.md`, or a spec document (e.g. `TIME_PARSING_RULES.md`, `TIMEZONE_EXTRACTION_RULES.md`). Tests verify that implementation matches architectural intent, not arbitrary behavior.

**Determinism First**  
All tests are deterministic: fixed timestamps, no network calls, mocked or in-memory dependencies. See `IMPLEMENTATION_CONSTRAINTS.md` § Verification.

**Layered Verification**  
- **Unit:** Isolated component logic (parser, extractor, resolver, converter, formatter)  
- **Contract:** Interface adherence (Core I/O, adapter mapping, DTO shapes)  
- **Flow:** End-to-end behaviour of `process()` with canonical inputs (golden cases)  
- **No UI/E2E** in MVP — platform-specific rendering and real network are out of scope.

---

## 2. Test Structure & Locations

All tests live under `tests/` (flat layout in MVP). Each test file states its specification source in the module docstring.

### 2.1. Core Unit Tests

**Purpose:** Verify isolated business logic against spec rules.

| Test File | What It Verifies | Specification Source |
|-----------|------------------|------------------------|
| `test_time_parser.py` | Time detection patterns, overlap priority, max results | `spec/TIME_PARSING_RULES.md` |
| `test_timezone_extractor.py` | Timezone hint matching, tie-breaking | `spec/TIMEZONE_EXTRACTION_RULES.md` |
| `test_timezone_resolver.py` | Precedence (explicit → user → channel → default) | `spec/POLICIES.md` §3 |
| `test_timezone_converter.py` | UTC conversion, DST, offset formatting, partial failure | `spec/CORE_CONTRACT.md`, `spec/POLICIES.md` §4 |

**Principle:** Each test maps to a documented rule or constraint; no behaviour is tested without a spec reference.

### 2.2. Flow / Golden Cases

**Purpose:** End-to-end verification of canonical scenarios from `END_TO_END_FLOW.md` and policy examples.

- **Location:** `tests/test_processor.py`  
- **Format:** Inline fixtures — `CoreMessageEvent` + `UserProfile` + `ChannelContext` + `city_index` + `config` → `process()` → assert on `DisplayBlock` or `None`.  
- **Coverage:** Explicit timezone, user/channel context, ambiguity → no reply, UTC offset display, partial flag, duplicate suppression (internal_message_id).

**Example (from `END_TO_END_FLOW.md`):**  
"See you at 10:30 Amsterdam" → `DisplayBlock` with Amsterdam first, local_time "10:30", second entry for active timezone (e.g. Yerevan).

### 2.3. Adapter & Contract Tests

**Purpose:** Verify architectural boundaries and adapter contracts.

| Test File | What It Verifies | Specification Source |
|-----------|------------------|------------------------|
| `test_processor.py` | Core I/O: `CoreMessageEvent` → `DisplayBlock \| None` | `spec/CORE_CONTRACT.md`, `END_TO_END_FLOW.md` |
| `test_event_mapping.py` | Platform event → `CoreMessageEvent`, internal IDs | `TELEGRAM_ADAPTER.md` §3 |
| `test_formatter.py` | DisplayBlock → formatted output (24h, timezone id, lines) | `ADAPTER_CONTRACTS.md` §6 |
| `test_adapter_config.py` | Config loading, schema, defaults | `ADAPTER_CONTRACTS.md` §5 |
| `test_user_loader.py` | User profile loading, timezone mapping | `USER_PROFILE_MODEL.md` |

---

## 3. Test Data Strategy

### 3.1. Deterministic Fixtures

- **Time:** Fixed `datetime` (e.g. `2026-01-25T12:00:00Z`) in tests; no `datetime.now()`.  
- **DST:** When relevant, use fixed dates (e.g. boundary in 2024 or 2026) for reproducible behaviour.  
- **Inputs:** Inline in test methods or `setUp`; no external data files required for MVP.

### 3.2. Edge Cases (covered where spec defines them)

- Timezone ambiguities (e.g. "10:30" with multiple possible TZ) → policy: no reply or safe resolution per `POLICIES.md`.  
- Empty/trivial inputs ("hello", bare "10") → no time detected or ambiguous per parsing rules.  
- Max limits (time mentions, timezones) → cap and, where applicable, `partial` flag per `CONTRACTS.md`.

### 3.3. Optional: Parameterized Testing

Time parsing and extraction can use `@pytest.mark.parametrize` or equivalent with explicit examples from `TIME_PARSING_RULES.md` / `TIMEZONE_EXTRACTION_RULES.md` to keep spec and tests in sync.

---

## 4. AI-Assisted Test Generation Protocol

When adding or changing behaviour:

1. **Read** the specification (e.g. `TIME_PARSING_RULES.md`, `POLICIES.md`).  
2. **Generate** test cases that cover all defined behaviours and branches.  
3. **Implement** code to pass the tests.  
4. **Run** tests; on failure, fix implementation or adjust tests to match spec (no spec-free behaviour).  
5. **Validate** that each new test corresponds to a stated rule or invariant.

**Quality gates:**

- Every rule in the spec that affects observable behaviour has ≥1 corresponding test.  
- Core DTOs and boundaries (Core I/O, adapter mapping) have contract-level tests.  
- All existing golden/processor cases continue to pass after changes.

---

## 5. Running & Coverage

### 5.1. Commands

```bash
# Run all tests (unittest)
python run_tests.py
# or
python -m unittest discover -s tests -p 'test_*.py' -v

# Run a single layer (by file)
python -m unittest tests.test_time_parser -v
python -m unittest tests.test_processor -v
python -m unittest tests.test_event_mapping tests.test_formatter -v
```

If using pytest:

```bash
pytest tests/ -v
pytest tests/test_time_parser.py tests/test_timezone_extractor.py -v
pytest --cov=src/core --cov-report=html tests/
```

### 5.2. Coverage Targets (MVP)

- **Core parsing/conversion:** High line coverage on `core/parser`, `core/timezone`, `core/processor`.  
- **Policy and ambiguity:** Branches that lead to `None` or to `DisplayBlock` covered.  
- **Contract:** All Core I/O and adapter contract tests passing.  
- **Golden:** All `test_processor.py` cases passing.

---

## 6. What We Don't Test (MVP Scope)

- **Platform UI:** Telegram/Discord rendering, keyboards, etc.  
- **Network/API:** All I/O and external services are mocked or avoided in tests.  
- **Performance/load:** Out of MVP scope.  
- **Non-deterministic behaviour:** No flaky time or random data in tests.

---

## 7. Verification Against Specifications

Each test file declares its specification source in the module docstring. Example:

```python
# test_time_parser.py
"""
Tests for time parser.
Specification: TIME_PARSING_RULES.md
"""

# test_processor.py
"""
Tests for core processor - golden test cases.
Specification: END_TO_END_FLOW.md, POLICIES.md
"""
```

Individual tests reference sections where useful (e.g. "Per TIME_PARSING_RULES.md §1.1", "CONTRACTS.md §DisplayBlock - partial flag"). This keeps tests traceable to the spec and makes it clear why each behaviour is tested.

---

**Summary:** Tests are derived from specifications; the testing pyramid is unit → contract → flow (golden). MVP keeps all tests under `tests/` with clear spec references and deterministic data only.

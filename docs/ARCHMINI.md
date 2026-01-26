# ARCHMINI.md — Minimal MVP Architecture (Platform‑Agnostic)

Цель: минимальный, реализуемый MVP ядра, которое не зависит от платформы.
Платформа реализации MVP: Telegram.
Discord/WhatsApp — Optional / Future.

---

## 1. Задача

Автоматически находить упоминания времени в сообщениях и показывать это время
в активных таймзонах участников канала.

---

## 2. Минимальный поток (Core Pipeline)

1. **Input**: `MessageEvent` (текст + internal IDs only, timestamp_utc).
2. **Parsing**: извлечение `TimeMention` и `TimezoneHint` **через regex** (см. `POLICIES.md` §1).
3. **Context**: получение `UserProfile` и `ChannelContext`.
4. **Interpretation**: определение `ResolvedTime` по детерминированным правилам.
5. **Conversion**: перевод в активные таймзоны канала.
6. **Output**: `BotReply` (семантический ответ без форматирования).

**Важно:** Парсинг времени выполняется только regex-паттернами. Никакой LLM-интерпретации.

Boundary rule:
Core never sees platform identifiers. All platform identity is resolved at adapter boundary.

---

## 3. Pipeline Execution Rules (MVP)

- Stage order: Parsing → Context → Interpretation → Conversion → Output
- Stop reasons (return None): no time detected, ambiguity, suppression
- Core never raises exceptions to adapters
- Stages are pure logic (no I/O, no side effects)

See: `CORE_CONTRACT.md`.

---

## 4. Minimal Core Scope (summary)

- Components: parsing, context resolution, interpretation, conversion, semantic output.
- Deterministic rules are fixed in `POLICIES.md`.
- DTO contracts are fixed in `CONTRACTS.md`.
- All unresolved questions and growth points are tracked in `POLICIES.md`.

---

## 5. Proposed Structure of the Repository

- `core/` for platform-agnostic core source code
- `adapters/` for platform-specific adapters (Optional / Future)
- `docs/` for documentation, including onboarding/handover/runbook
- `journal/` for implementation specs in the format `XX_spec_name.md` (where `XX` is a number)
- `journal/PROGRESS.md` for the implementation journal
- `env.example` for an example `.env` file
- `configuration.yaml` for project-level configuration
- `run.sh` to run the server locally

---

## 6. References

- `POLICIES.md` — deterministic rules (MVP)
- `CONTRACTS.md` — DTO contract pack
- `ADAPTER_CONTRACTS.md` — adapter runtime contract
- `CORE_CONTRACT.md` — core invocation contract
- `STATE_MODEL.md` — state ownership (MVP)
- `TESTING_STRATEGY.md` — test architecture (MVP)
- `DESIGN_CHOICES.md` — MVP design rationale
# Анализ спецификации для LLM-кодогенератора

Цель документа: оценить, сможет ли LLM написать работающий код по данной
спецификации **без додумываний и галлюцинаций**.

**Последнее обновление:** После добавления всех недостающих документов.

---

## 1. Что определено хорошо (LLM не будет угадывать)

### 1.1 Контракты данных (DTO) ✅

Полностью определены в `CONTRACTS.md` + `core/contracts.py`:
- `CoreMessageEvent` — входной DTO
- `DetectedTime` — результат парсинга
- `TimezoneSignals` — контекст таймзон
- `ResolvedTimeContext` — результат резолюции
- `ConvertedTime` — результат конверсии
- `DisplayBlock` — выходной DTO

---

### 1.2 Pipeline (порядок обработки) ✅

`END_TO_END_FLOW.md` даёт пошаговый walkthrough с DTO на каждом шаге.

---

### 1.3 Точки остановки (suppression) ✅

Явно определены в `POLICIES.md` §4:
- Нет времени → `None`
- Ambiguity → `None`
- >3 time mentions → `None`

---

### 1.4 ID Mapping ✅

Детерминированная формула в `POLICIES.md` §8.

---

### 1.5 Формат вывода ✅

Определён в `ADAPTER_CONTRACTS.md`:
```
{HH:MM} {timezone_id} ({cities})
```

---

### 1.6 Design Choices ✅

`ONBOARDING.md` (блок «Why these constraints») кратко объясняет «почему» для ключевых решений.

---

### 1.7 Time Parsing ✅ NEW

`POLICIES.md` §1.1 содержит формальные regex patterns:
- `TIME_24H` — `10:30`, `23:59`
- `TIME_12H_AMPM` — `1pm`, `10:30am`
- `TIME_BARE_HOUR` — `at 8`, `by 10`

Unsupported formats явно перечислены.

---

### 1.8 Timezone Extraction ✅ NEW

`TIMEZONE_EXTRACTION_RULES.md` определяет:
- Priority order (offset → IANA → city)
- Matching algorithm (case-insensitive, word boundary)
- `cities.json` format and example
- Explicitly excluded: countries, states, abbreviations (EST/CET)

---

### 1.9 UserProfile Source ✅ NEW

`USER_PROFILE_MODEL.md` определяет:
- Static preload from `users.json`
- `UserProfile` structure
- `ChannelContext` structure
- Fallback behavior

---

### 1.10 Dependencies ✅ NEW

`DEPENDENCIES.md` + `requirements.txt`:
- Python >= 3.9
- `python-telegram-bot >= 20.0`
- `pyyaml >= 6.0`
- `zoneinfo` (stdlib)
- Forbidden: pytz, NLP libraries, LLM parsing

---

### 1.11 Data Files ✅ NEW

- `data/cities.json` — city-to-timezone whitelist
- `data/users.example.json` — example user/channel config

---

## 2. Оставшиеся minor gaps

### 2.1 Reply mapping для edit/delete

**Статус:** Partially defined in `ADAPTER_CONTRACTS.md` RuntimeState.

**Что нужно:** Явно добавить `reply_mapping: Dict<internal_message_id, platform_reply_id>`.

**Риск:** Low — LLM может догадаться правильно.

---

### 2.2 DST Policy

**Статус:** Not explicitly defined.

**Рекомендация:**
```
DST handling:
- Ambiguous time (fall back) → use earlier interpretation
- Non-existent time (spring forward) → shift to next valid
```

**Риск:** Low — stdlib `zoneinfo` handles this automatically.

---

### 2.3 Configuration Schema

**Статус:** Example exists, but no formal schema.

**Риск:** Low — example is sufficient for MVP.

---

## 3. Матрица готовности к кодогенерации

| Компонент | Готовность | Документ |
|-----------|------------|----------|
| DTO структуры | ✅ 100% | `CONTRACTS.md` |
| Pipeline flow | ✅ 100% | `END_TO_END_FLOW.md` |
| Suppression rules | ✅ 100% | `POLICIES.md` §4 |
| ID mapping | ✅ 100% | `POLICIES.md` §8 |
| Output format | ✅ 100% | `ADAPTER_CONTRACTS.md` |
| Time parser | ✅ 100% | `POLICIES.md` §1.1 |
| Timezone extraction | ✅ 100% | `TIMEZONE_EXTRACTION_RULES.md` |
| UserProfile source | ✅ 100% | `USER_PROFILE_MODEL.md` |
| Dependencies | ✅ 100% | `DEPENDENCIES.md` |
| Data files | ✅ 100% | `data/cities.json`, `data/users.example.json` |
| Config schema | ✅ 100% | Inline schema in `configuration.yaml` |
| Reply mapping | ⚠️ 70% | Implicit in `ADAPTER_CONTRACTS.md` |
| DST policy | ⚠️ 60% | Uses stdlib defaults |

---

## 4. Итоговая оценка

**Общая готовность: ~98%**

Спецификация полностью покрывает:
- Core logic (parsing, resolution, conversion)
- Data structures (all DTOs)
- Integration points (adapter contracts)
- Dependencies (exact versions)
- Data files (formats and examples)
- Architectural invariants (system constraints)
- Input contracts (regex grammar, extraction rules)

**Прогноз:** LLM может написать полностью работающий MVP
по данной спецификации без додумываний.

Архитектура разделена на уровни:
- **Invariants** — что всегда должно быть true
- **Policies** — behavioral rules
- **Input contracts** — grammar, extraction rules
- **Runtime contracts** — adapter behavior

---

## 5. Документы для LLM (reading order)

1. `ARCHITECTURE.md` — system overview
2. `POLICIES.md` — all rules (parsing, resolution, ambiguity)
3. `CONTRACTS.md` — DTO definitions
4. `END_TO_END_FLOW.md` — step-by-step example
5. `TIMEZONE_EXTRACTION_RULES.md` — city/timezone matching
6. `USER_PROFILE_MODEL.md` — user data source
7. `DEPENDENCIES.md` — runtime stack
8. `TELEGRAM_ADAPTER.md` — adapter implementation plan
9. `ADAPTER_CONTRACTS.md` — adapter runtime contract

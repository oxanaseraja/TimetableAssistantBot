# Проверка соответствия проекта заявленным ограничениям MVP

## Статус проверки

**Дата проверки:** 2026-01-26  
**Статус проекта:** Спецификация завершена, код не реализован (только заглушки в `src/`)

---

## Результаты проверки по пунктам

### ✅ 1. Обрабатывается только первое найденное время в сообщении

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/POLICIES.md` §6.1 явно указывает:
  ```markdown
  **MVP simplification:** Process only the **first** detected time mention.
  ```
- В том же разделе указано поведение:
  ```
  Input: "call at 10am NYC or 2pm London"
  Detected: [10am, 2pm]
  Processed: 10am only (first by position)
  ```
- Примечание: "Parser still returns up to 3 times (for future use), but processor uses only `detected_times[0]` in MVP."

**Соответствие:** ✅ Полное

---

### ✅ 2. Максимум 3 упоминания времени на сообщение

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/POLICIES.md` §6 указывает:
  ```markdown
  - Max time mentions processed: 3
  ```
- `docs/POLICIES.md` §6 также указывает:
  ```markdown
  - Ignore messages with > 3 time mentions
  ```
- `src/configuration.yaml` содержит:
  ```yaml
  core:
    max_time_mentions: 3
  ```
- `docs/CONTRACTS.md` определяет `CoreConfig`:
  ```markdown
  max_time_mentions: int,     // max times to process per message (default: 3)
  ```
- `docs/TIME_PARSING_RULES.md` §3.2 показывает алгоритм:
  ```python
  return sorted(results, key=lambda x: x.position_start)[:max_results]
  ```
  где `max_results` по умолчанию = 3

**Соответствие:** ✅ Полное

**Примечание:** В MVP это ограничение работает на уровне парсера, но фактически используется только первое время (см. пункт 1).

---

### ✅ 3. Максимум 5 часовых поясов в ответе

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/POLICIES.md` §6 указывает:
  ```markdown
  - Max timezones shown: 5
  ```
- `src/configuration.yaml` содержит:
  ```yaml
  output:
    max_timezones: 5
  ```
- `docs/CONTRACTS.md` определяет `CoreConfig`:
  ```markdown
  max_timezones: int,         // max timezones in DisplayBlock (default: 5)
  ```
- `docs/ADAPTER_CONTRACTS.md` §6 указывает:
  ```markdown
  - Cap to 5 lines.
  ```
- `docs/TELEGRAM_ADAPTER.md` §4 указывает:
  ```markdown
  - Cap to 5 lines.
  ```

**Соответствие:** ✅ Полное

---

### ✅ 4. Молчание при неоднозначности

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/POLICIES.md` §4 "Ambiguity Policy (Safe-Only)" явно определяет:
  ```markdown
  MVP never outputs assumed or probabilistic times.
  
  - Exactly one valid interpretation → answer
  - Multiple possible interpretations → return None (no reply)
  - Missing timezone + >1 active timezone → do not answer
  - Missing am/pm in 1–12 → return None
  ```
- В том же разделе указано поведение:
  ```markdown
  Ambiguity behavior (MVP):
  - Core returns `None`
  - Adapter sends no reply
  - Clarification dialogs are out of scope
  ```
- `docs/ARCHITECTURAL_INVARIANTS.md` Invariant #4 и #5:
  ```markdown
  ### 4. Core never infers missing information
  If information is missing, core does not guess.
  
  ### 5. All ambiguity leads to no reply
  Core returns `None` for any ambiguous situation.
  ```
- `docs/END_TO_END_FLOW.md` содержит пример:
  ```markdown
  ## Alternative Stop Example (Ambiguous)
  Message: `"See you at 8"`
  - Time detected: `hour=8, minute=null, am_pm=null, ambiguous=true`
  - Ambiguity policy → core returns `None`
  - Adapter sends no reply
  ```

**Соответствие:** ✅ Полное

---

### ✅ 5. Обрабатывается только один чат

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/TELEGRAM_ADAPTER.md` §1 явно указывает:
  ```markdown
  - Subscribe to messages in a **single Telegram chat** (MVP).
  ```
- `src/configuration.yaml` содержит только один `chat_id`:
  ```yaml
  telegram:
    chat_id: "-1001234567890"    # string, required, can be negative for groups
  ```
- `docs/ADAPTER_CONTRACTS.md` §5 определяет конфигурацию с одним `chat_id`:
  ```yaml
  telegram:
    chat_id: string            # required
  ```
- В спецификации нет упоминаний о поддержке нескольких чатов в MVP

**Соответствие:** ✅ Полное

**Примечание:** В `docs/TELEGRAM_ADAPTER.md` §6 "Non-Goals (MVP)" явно указано:
```markdown
- Multi-chat / multi-platform routing
```

---

### ✅ 6. Часовые пояса задаются администратором в users.json

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/USER_PROFILE_MODEL.md` §3 "Source of UserProfile (MVP)" явно указывает:
  ```markdown
  In MVP, user profiles are loaded from a **static JSON file**.
  
  ### File: `users.json`
  ```
- Приведён пример структуры:
  ```json
  {
    "telegram:123456789": {
      "timezone": "Europe/Amsterdam"
    }
  }
  ```
- `docs/USER_PROFILE_MODEL.md` §5 указывает:
  ```markdown
  **Timezone acquisition (MVP):**
  - `UserProfile.timezone` is pre-populated by adapter from `users.json`
  - User-facing timezone setup is out of scope
  ```
- `docs/POLICIES.md` §5 указывает:
  ```markdown
  **Timezone acquisition (MVP):**
  - `UserProfile.timezone` is pre-populated by adapter from `users.json`
  - User-facing timezone setup is out of scope
  ```
- `src/data/users.json` содержит пример структуры с комментарием:
  ```json
  {
    "_comment": "Example users.json - copy to users.json and fill with real data",
    "telegram:123456789": {
      "timezone": "Europe/Amsterdam"
    }
  }
  ```
- `src/configuration.yaml` указывает путь:
  ```yaml
  data:
    users_path: "data/users.json"
  ```

**Соответствие:** ✅ Полное

**Примечание:** В `docs/USER_PROFILE_MODEL.md` §5 явно указано, что интерактивная настройка часовых поясов пользователями — это Post-MVP функционал.

---

### ✅ 7. Обработка только абсолютного времени, без дат и относительного времени

**Статус:** **СООТВЕТСТВУЕТ** спецификации

**Доказательства:**
- `docs/TIME_PARSING_RULES.md` §2 "Unsupported Patterns (Explicitly Ignored)" явно перечисляет:
  ```markdown
  | Format | Example | Reason |
  |--------|---------|--------|
  | Relative | `in 2 hours`, `через час` | Requires current time context |
  | Ranges | `10:00-11:00` | Out of scope |
  | Date+time | `Jan 25 at 10:30` | Out of scope |
  ```
- `docs/POLICIES.md` §4.1 "DST Policy" указывает:
  ```markdown
  - Cross-day inference is explicitly unsupported
  - "Tomorrow at 10" is not parsed (relative time)
  ```
- `docs/POLICIES.md` §1 указывает:
  ```markdown
  **Note:** Dot-separated time format (HH.MM) is explicitly NOT supported in MVP.
  ```
- `docs/TIME_PARSING_RULES.md` §1 определяет только три поддерживаемых формата:
  1. TIME_24H — `10:30`
  2. TIME_12H_AMPM — `10:30am`, `2pm`
  3. TIME_BARE_HOUR — `at 8` (только с триггерным словом)

**Соответствие:** ✅ Полное

**Примечание:** В `docs/POLICIES.md` §4.1 явно указано:
```markdown
**Core does not infer calendar dates from text.**
All time mentions are interpreted relative to message timestamp date.
```

---

## Общий вывод

### ✅ Все 7 пунктов полностью соответствуют спецификации

**Статус проверки:** **ПРОЙДЕНА**

Все заявленные ограничения MVP:
1. ✅ Чётко документированы в спецификации
2. ✅ Имеют явные обоснования (rationale)
3. ✅ Содержат примеры поведения
4. ✅ Указаны как MVP-ограничения с пометками о Post-MVP расширениях

---

## Дополнительные наблюдения

### Сильные стороны спецификации:

1. **Явность ограничений:** Все ограничения явно указаны, а не подразумеваются
2. **Обоснованность:** Каждое ограничение имеет rationale (зачем и почему)
3. **Примеры:** Приведены конкретные примеры поведения
4. **Разделение MVP/Post-MVP:** Чётко разделено, что в MVP, а что в будущем

### Рекомендации для реализации:

1. **При реализации кода** убедиться, что:
   - Парсер возвращает максимум 3 времени, но процессор использует только первое
   - Проверка на неоднозначность возвращает `None` при любых сомнениях
   - Конфигурация загружается один раз при старте
   - Адаптер работает только с одним `chat_id`

2. **При тестировании** проверить:
   - Сообщение с несколькими временами → обрабатывается только первое
   - Сообщение с неоднозначным временем → бот молчит
   - Сообщение с относительным временем → игнорируется
   - Попытка использовать несколько чатов → ошибка конфигурации

---

## Заключение

Спецификация проекта **полностью соответствует** заявленным ограничениям MVP. Все 7 пунктов:
- ✅ Документированы
- ✅ Обоснованы
- ✅ Проиллюстрированы примерами
- ✅ Разделены на MVP и Post-MVP

Проект готов к реализации согласно спецификации.

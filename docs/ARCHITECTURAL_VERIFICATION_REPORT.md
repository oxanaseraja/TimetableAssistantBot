# Architectural Verification Report

**Дата:** 2026-01-24  
**Scope:** Полная верификация всех spec-документов  
**Метод:** Peer review на соответствие, непротиворечивость и LLM-safety

---

## Резюме

| Категория | Найдено проблем | Критических | Требует уточнения |
|-----------|-----------------|-------------|-------------------|
| Логические циклы | 0 | 0 | 0 |
| Скрытые противоречия | 4 | 1 | 3 |
| Недоопределённые контракты | 7 | 2 | 5 |
| Потенциальные галлюцинации | 5 | 1 | 4 |

**Общая оценка:** Спецификация высокого качества (~95%), но есть точечные проблемы.

---

# 1. ЛОГИЧЕСКИЕ ЦИКЛЫ

## Статус: ✅ Циклов не обнаружено

Проверена иерархия зависимостей документов:

```
ARCHITECTURAL_INVARIANTS.md (root)
├── POLICIES.md
│   ├── TIME_PARSING_RULES.md
│   ├── TIMEZONE_EXTRACTION_RULES.md
│   └── USER_PROFILE_MODEL.md
├── CONTRACTS.md
├── CORE_CONTRACT.md
└── ADAPTER_CONTRACTS.md
    └── TELEGRAM_ADAPTER.md
```

Все ссылки однонаправленные. Циклических зависимостей нет.

---

# 2. СКРЫТЫЕ ПРОТИВОРЕЧИЯ

## 2.1 🔴 КРИТИЧЕСКОЕ: cities в DisplayBlock — кто заполняет?

**Документы в конфликте:**
- `TELEGRAM_ADAPTER.md` §4: "Ignore `cities` in MVP (`cities = []`)"
- `END_TO_END_FLOW.md` Step 5: `cities: ["Amsterdam"]`
- `POLICIES.md` §8: "Adapter populates `cities` from local city list"
- `ADAPTER_CONTRACTS.md` §6: "Cities shown in parentheses if present"

**Противоречие:**
- TELEGRAM_ADAPTER.md говорит игнорировать cities
- Все остальные документы говорят использовать cities

**Рекомендация:** Удалить устаревшую строку из TELEGRAM_ADAPTER.md:
```diff
- - Ignore `cities` in MVP (`cities = []`).
+ - Cities loaded from local list, grouped by timezone, sorted alphabetically.
```

---

## 2.2 ⚠️ Формат ID mapping — разные формулы

**Документы:**
- `POLICIES.md` §8: `sha256(f"telegram:{platform_user_id}")`
- `TELEGRAM_ADAPTER.md` §3: `SHA256(f"telegram:{telegram_user_id}")`
- `END_TO_END_FLOW.md` Step 0: `SHA256("telegram:123")`

**Проблема:** Разный синтаксис (sha256 vs SHA256, f-string vs обычная строка)

**Фактически:** Это одно и то же, но LLM может интерпретировать по-разному.

**Рекомендация:** Унифицировать везде:
```python
internal_user_id = hashlib.sha256(f"telegram:{platform_user_id}".encode()).hexdigest()
```

---

## 2.3 ⚠️ Формат internal_message_id — разные формулы

**Документы:**
- `POLICIES.md` §8: `sha256(f"{platform_chat_id}:{platform_message_id}")`
- `TELEGRAM_ADAPTER.md` §3: `SHA256(f"{telegram_chat_id}:{telegram_message_id}")`
- `END_TO_END_FLOW.md`: `SHA256("‑1001:555")` (использует специальный символ ‑ вместо -)

**Проблема:** В END_TO_END_FLOW.md используется Unicode MINUS (U+2011) вместо ASCII hyphen.

**Рекомендация:** Исправить на обычный дефис в END_TO_END_FLOW.md.

---

## 2.4 ⚠️ Сигнатура process() — разные аргументы

**Документы:**
- `CORE_CONTRACT.md`: `process(event: CoreMessageEvent) -> DisplayBlock | None`
- `END_TO_END_FLOW.md`: Показывает, что нужны также UserProfile и ChannelContext

**Проблема:** Откуда core получает UserProfile и ChannelContext?

**Варианты интерпретации:**
1. Core получает их как дополнительные аргументы
2. Core получает их через event
3. Adapter встраивает их в event

**Рекомендация:** Уточнить сигнатуру:
```python
process(
    event: CoreMessageEvent,
    user_profile: UserProfile,
    channel_context: ChannelContext
) -> DisplayBlock | None
```

---

# 3. НЕДООПРЕДЕЛЁННЫЕ КОНТРАКТЫ

## 3.1 🔴 КРИТИЧЕСКОЕ: Как core получает UserProfile и ChannelContext?

**Проблема:** 
- `CORE_CONTRACT.md` определяет только `process(event)`
- `USER_PROFILE_MODEL.md` говорит "Core receives as input from adapter"
- Но механизм передачи не определён

**LLM может:**
- Добавить глобальный контекст
- Добавить аргументы в process()
- Добавить поля в CoreMessageEvent

**Рекомендация:** Добавить в `CORE_CONTRACT.md`:
```md
## Full Interface

```python
def process(
    event: CoreMessageEvent,
    user_profile: UserProfile,
    channel_context: ChannelContext
) -> DisplayBlock | None
```

Adapter is responsible for constructing UserProfile and ChannelContext
before calling core.
```

---

## 3.2 🔴 КРИТИЧЕСКОЕ: Как вычисляется active_timezones?

**Проблема:**
- `POLICIES.md` §5: "ActiveTimezoneSet = all known user timezones present in channel context"
- `USER_PROFILE_MODEL.md` §6: "active_timezones = timezones of all members listed in channel"

**Не определено:**
1. Кто вычисляет active_timezones — core или adapter?
2. Когда — при каждом сообщении или при старте?
3. Формула вычисления

**Рекомендация:** Добавить явный алгоритм:
```python
def compute_active_timezones(channel: ChannelContext, users: Dict[str, UserProfile]) -> List[str]:
    timezones = set()
    for member_id in channel.members:
        if member_id in users and users[member_id].timezone:
            timezones.add(users[member_id].timezone)
    return sorted(list(timezones))
```

---

## 3.3 ⚠️ Как обрабатывать несколько времён в одном сообщении?

**Проблема:**
- `TIME_PARSING_RULES.md`: Возвращает до 3 DetectedTime
- `END_TO_END_FLOW.md`: Показывает только одно время

**Не определено:**
1. Каждое время обрабатывается отдельно?
2. Один DisplayBlock на все времена или несколько?
3. Как timezone hint применяется к нескольким временам?

**Рекомендация:** Добавить пример с несколькими временами в END_TO_END_FLOW.md.

---

## 3.4 ⚠️ Формат timestamp_utc

**Проблема:**
- `CONTRACTS.md`: `timestamp_utc: datetime`
- `END_TO_END_FLOW.md`: `"2026-01-25T12:00:00Z"` (строка)

**Не определено:**
1. datetime object или ISO string?
2. Если datetime — aware или naive?
3. Используется ли вообще в core?

**Рекомендация:** Уточнить в CONTRACTS.md:
```md
timestamp_utc: datetime  # timezone-aware, UTC
```

---

## 3.5 ⚠️ Что такое "partial" в DisplayBlock.flags?

**Документы:**
- `CONTRACTS.md`: `partial: boolean`
- `END_TO_END_FLOW.md`: `partial: false`

**Не определено:**
- Когда partial = true?
- Что это значит?
- Как adapter должен реагировать?

**Рекомендация:** Определить или удалить:
```md
partial: boolean  # true if some timezones were omitted due to max limit
```

---

## 3.6 ⚠️ ordering в DisplayBlock — enum или string?

**Проблема:**
- `END_TO_END_FLOW.md`: `ordering: "SOURCE_THEN_CHANNEL_DEFAULT_THEN_OFFSET_ASC"`
- `POLICIES.md` §6: Описывает правила, но не enum

**Не определено:**
1. Какие значения допустимы?
2. Это enum или free-form string?
3. Используется ли adapter'ом или только для документации?

**Рекомендация:** Добавить enum в CONTRACTS.md:
```md
ordering: "SOURCE_FIRST" | "OFFSET_ASC" | "ALPHABETICAL"
```

---

## 3.7 ⚠️ Токенизация в timezone extraction

**Проблема:**
- `TIMEZONE_EXTRACTION_RULES.md` §3: `for word in tokenize(context)`

**Не определено:**
1. Как tokenize() разбивает текст?
2. Разделители: пробелы? пунктуация?
3. Что делать с "in Amsterdam" — это один токен или два?

**Рекомендация:** Добавить определение:
```python
def tokenize(text: str) -> List[str]:
    # Split by whitespace and punctuation, keep words only
    return re.findall(r'\b\w+\b', text)
```

---

# 4. ПОТЕНЦИАЛЬНЫЕ ГАЛЛЮЦИНАЦИИ

## 4.1 🔴 КРИТИЧЕСКОЕ: Алгоритм overlap detection в парсере

**Проблема:**
- `TIME_PARSING_RULES.md` §3: `if not overlaps(match, results)`

**Не определено:**
1. Функция `overlaps()` не определена
2. Как определить перекрытие позиций?

**LLM может:**
- Реализовать по-своему
- Проигнорировать overlap check
- Создать баги с перекрывающимися паттернами

**Рекомендация:** Добавить определение:
```python
def overlaps(match, existing_results: List[DetectedTime]) -> bool:
    for r in existing_results:
        if not (match.end() <= r.position_start or match.start() >= r.position_end):
            return True
    return False
```

---

## 4.2 ⚠️ Regex для TIME_BARE_HOUR неполный

**Проблема:**
- `TIME_PARSING_RULES.md` §1.3: `(trigger_word)\s+([1-9]|1[0-2])\b`

**Не определено:**
1. Точный список trigger words как regex alternation
2. Case sensitivity

**Рекомендация:** Дать полный regex:
```python
TRIGGER_WORDS = r'(?:at|by|around|about|until|till)'
TIME_BARE_HOUR = rf'(?i){TRIGGER_WORDS}\s+([1-9]|1[0-2])\b'
```

---

## 4.3 ⚠️ Normalize offset — алгоритм не определён

**Проблема:**
- `TIMEZONE_EXTRACTION_RULES.md` §1.1: "Normalize to ±HH:MM format internally"
- §3: `return normalize_offset(match)`

**Не определено:**
1. Как нормализовать `+3` → `+03:00`?
2. Как нормализовать `+0300` → `+03:00`?

**Рекомендация:** Добавить алгоритм:
```python
def normalize_offset(raw: str) -> str:
    # Remove UTC/GMT prefix
    raw = re.sub(r'^(UTC|GMT)', '', raw, flags=re.IGNORECASE)
    
    # Parse hours and minutes
    if ':' in raw:
        sign, hours, minutes = re.match(r'([+-])(\d{1,2}):(\d{2})', raw).groups()
    elif len(raw) >= 4:
        sign, hours, minutes = raw[0], raw[1:3], raw[3:5] if len(raw) > 3 else '00'
    else:
        sign, hours, minutes = raw[0], raw[1:], '00'
    
    return f"{sign}{int(hours):02d}:{minutes}"
```

---

## 4.4 ⚠️ Как core узнаёт текущую дату для DST?

**Проблема:**
- Конверсия времени зависит от DST
- DST зависит от даты
- `CoreMessageEvent` содержит `timestamp_utc`

**Не определено:**
1. Используется ли timestamp_utc для определения DST?
2. Или используется дата "сегодня"?
3. Что если сообщение о времени "завтра"?

**Рекомендация:** Добавить в POLICIES.md:
```md
## DST Policy

Time is assumed to be on the same date as message timestamp.
Future dates are out of scope.
Core uses timestamp_utc.date() as reference date for DST calculation.
```

---

## 4.5 ⚠️ Что если город в тексте, но не рядом с временем?

**Проблема:**
- `TIMEZONE_EXTRACTION_RULES.md` §3: `context = text[position-window : position+window]`
- window = 30 chars

**Не определено:**
1. Что если "Amsterdam" в начале, а "10:30" в конце длинного сообщения?
2. Применяется ли hint ко всем временам в сообщении?

**Рекомендация:** Уточнить:
```md
Timezone hint applies only to the time mention within ±30 chars window.
Each time mention has its own independent timezone resolution.
```

---

# 5. РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ

## Приоритет 1 (Критические)

| # | Проблема | Документ | Исправление |
|---|----------|----------|-------------|
| 2.1 | cities contradiction | TELEGRAM_ADAPTER.md | Удалить устаревшую строку |
| 3.1 | process() signature | CORE_CONTRACT.md | Добавить UserProfile, ChannelContext |
| 3.2 | active_timezones | USER_PROFILE_MODEL.md | Добавить алгоритм вычисления |
| 4.1 | overlaps() undefined | TIME_PARSING_RULES.md | Добавить определение функции |

## Приоритет 2 (Важные)

| # | Проблема | Документ | Исправление |
|---|----------|----------|-------------|
| 2.2 | ID mapping syntax | Все | Унифицировать формат |
| 2.3 | Unicode minus | END_TO_END_FLOW.md | Заменить на ASCII |
| 3.7 | tokenize() | TIMEZONE_EXTRACTION_RULES.md | Добавить определение |
| 4.2 | trigger words regex | TIME_PARSING_RULES.md | Дать полный regex |
| 4.3 | normalize_offset | TIMEZONE_EXTRACTION_RULES.md | Добавить алгоритм |

## Приоритет 3 (Улучшения)

| # | Проблема | Документ | Исправление |
|---|----------|----------|-------------|
| 3.3 | Multiple times | END_TO_END_FLOW.md | Добавить пример |
| 3.4 | timestamp_utc format | CONTRACTS.md | Уточнить тип |
| 3.5 | partial flag | CONTRACTS.md | Определить или удалить |
| 3.6 | ordering enum | CONTRACTS.md | Добавить enum |
| 4.4 | DST date | POLICIES.md | Добавить политику |
| 4.5 | Hint scope | TIMEZONE_EXTRACTION_RULES.md | Уточнить |

---

# 6. ЗАКЛЮЧЕНИЕ

Спецификация находится на **высоком уровне качества** (95%+).

**Сильные стороны:**
- Чёткое разделение ответственности (core vs adapter)
- Детерминированные правила (regex, whitelist)
- Явные инварианты (23 штуки)
- Хорошие примеры (END_TO_END_FLOW.md)

**Слабые места:**
- Несколько мелких противоречий между документами
- Некоторые алгоритмы определены словами, но не кодом
- Сигнатура process() неполная

**Рекомендация:**
Исправить 4 критические проблемы перед передачей LLM на реализацию.
Остальные проблемы не блокируют, но повышают риск неоднозначной интерпретации.

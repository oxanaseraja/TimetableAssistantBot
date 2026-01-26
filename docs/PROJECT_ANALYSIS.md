# Анализ проекта: соответствие тестовому заданию (MVP)

Этот проект — **архитектурное MVP**, где основной фокус на формализации
контрактов и детерминированных правил, чтобы LLM могла реализовать систему
без додумываний.

---

## 1. Что уже соответствует требованиям задания

**Архитектура и контракты**
- `ARCHMINI.md` фиксирует границы и pipeline.
- `POLICIES.md` закрывает все ключевые правила.
- `CONTRACTS.md` описывает DTO и форматы.
- `CORE_CONTRACT.md` фиксирует интерфейс core.
- `ADAPTER_CONTRACTS.md` описывает runtime контракт адаптера.
- `TELEGRAM_ADAPTER.md` даёт детерминированный план интеграции.

**LLM‑safe формализация**
- Safe‑only ambiguity (core returns None, adapter sends no reply).
- Единая формула ID mapping (SHA256, стабильный input).
- Однозначный формат вывода (24‑часовой, IANA id, города в скобках).

**Design choices**
- `DESIGN_CHOICES.md` фиксирует “почему” (trade‑offs и rationale).

---

## 2. Что намеренно вне MVP (explicit out of scope)

Эти пункты не требуются для архитектурного MVP и задекларированы как out of scope:
- Реализация Telegram‑бота (код адаптера)
- UX‑флоу установки таймзоны пользователем
- Dialog/clarification flows
- Персистентное хранилище
- Мультиплатформенность
- Полный набор тестов

---

## 3. Потенциальные риски (но они уже закрыты архитектурно)

### 3.1 ActiveTimezoneSet без storage
**Решение:** ActiveTimezoneSet = all user timezones in ChannelContext.
Activity tracking и decay не используются в MVP.

### 3.2 Ambiguity handling
**Решение:** Core returns None, adapter sends no reply. Диалоги out of scope.

### 3.3 Cities в выводе
**Решение:** Cities берутся из локального списка адаптера.
IANA timezone остаётся главным идентификатором.

---

## 4. Что нужно для продакшн‑версии (не часть MVP)

- Полный Telegram адаптер
- Реальный storage (UserProfile/ChannelContext)
- Тестовое покрытие
- Runtime/ops (monitoring, deploy)

---

## 5. Итог

Проект соответствует цели тестового задания: **архитектурная спецификация,**
которая делает реализацию детерминированной и защищённой от “додумываний”.
Код и эксплуатационные аспекты намеренно вынесены за пределы MVP.

See: `DOC_INDEX.md` for the full document map.

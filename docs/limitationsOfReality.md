В реальном продукте:

❗ НЕЛЬЗЯ автоматически узнать timezone пользователя при входе в чат.

Единственные реальные варианты:
Вариант A — ручная регистрация
пользователь пишет: /timezone Europe/Amsterdam
или кнопка
или onboarding

Вариант B — админ загружает список
файл users.json
маппинг user_id → timezone



Platform APIs do not provide user timezone automatically.
Therefore, timezone must be obtained via explicit user input or external configuration.
Automatic onboarding and timezone collection are product-layer features and out of scope for MVP.
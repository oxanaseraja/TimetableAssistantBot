# ARCH_DIAGRAM.md — System Architecture (Snapshot View)

This diagram shows blocks, dependencies, and extension points.

```
┌───────────────────────────────┐
│           ADAPTERS            │
│  Telegram (MVP)               │
│  Discord / WhatsApp (Future)  │
└──────────────┬────────────────┘
               │ CoreMessageEvent
               ▼
┌───────────────────────────────┐
│            CORE               │
│  Parsing → Context → Resolve  │
│  → Convert → DisplayBlock     │
└──────────────┬────────────────┘
               │ DisplayBlock | None
               ▼
┌───────────────────────────────┐
│        ADAPTER OUTPUT         │
│  Format + Send reply          │
└───────────────────────────────┘
```

---

## Dependencies

- Adapters depend on:
  - `ADAPTER_CONTRACTS.md`
  - `CONTRACTS.md`
  - `CORE_CONTRACT.md`

- Core depends on:
  - `POLICIES.md`
  - `CONTRACTS.md`

---

## Extension Points

- Add new adapters under `adapters/`
- Add storage layer (production)
- Extend parser rules (policy updates)

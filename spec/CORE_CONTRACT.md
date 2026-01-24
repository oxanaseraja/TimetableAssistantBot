# CORE_CONTRACT.md — Core Invocation Interface (MVP)

This document defines how adapters invoke the core.

---

## CoreProcessor Interface

```
process(event: CoreMessageEvent) -> DisplayBlock | None
```

Rules:
- Synchronous call.
- Pure function (no side effects, no I/O).
- Core never raises exceptions to the adapter.
- `None` means: no output (no time, ambiguity, suppression).

Adapter obligations:
- If `None`, send nothing.
- Adapter never formats without a `DisplayBlock`.

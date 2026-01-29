# RUNNING.md — How to Run

This document describes execution from the **specification** perspective: the core has no standalone entrypoint; the full application is run via the implementation in `src/`.

---

## Core (Platform-Agnostic Library)

**Requirements:** Python 3.9+ (see `../DEPENDENCIES.md`).

**Install:** No external dependencies are required for the minimal core (stdlib only).

**Run:** There is no executable entrypoint in the MVP core. The core is used as a library (e.g. by the adapter or by tests). See documentation and tests for usage.

---

## Full Application (Telegram Adapter)

To run the bot: see `src/README.md` (Quick Start) or run `src/run.sh` from the project root. Requires `TELEGRAM_TOKEN`, `configuration.yaml`, and data files per `../config_schema.md` and `../ADAPTER_CONTRACTS.md`.

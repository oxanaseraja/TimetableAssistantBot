## Configuration Schema (MVP)

This document defines the expected structure of `configuration.yaml`.
It is a human-readable schema for validation and onboarding.

**Environment variables:** Values may use `${VAR_NAME}` or `${VAR_NAME:default_value}`; resolved at load time (see adapter config loader).

### Root

- Type: object (YAML mapping)
- If root is `null` or not a mapping, it is treated as `{}` (warning logged if not a mapping).

### Sections

#### `telegram`

- `token` (string, required)
  - May be empty in config if provided via env `TELEGRAM_TOKEN`.
- `chat_id` (string or int, required)
- `retry_attempts` (int, optional, default: 3, range: 1..10)
- `max_lines` (int, optional, default: 5, range: 1..10)
- `persistence_path` (string or null, optional)

#### `data`

- `cities_path` (string, required)
- `users_path` (string, required)

Environment fallback:
- `DATA_PATHS="path/to/cities.json,path/to/users.json"` may supply both paths

#### `core`

- `max_time_mentions` (int, optional, default: 3, range: 1..10)
- `default_timezone` (string or null, optional, default: null)
  - If `null` or `"UTC"` → treated as UTC fallback.
  - Must be a valid IANA timezone if provided.

#### `output`

- `max_timezones` (int, optional, default: 5, range: 1..10)
- `ordering` (string, optional, default: `"SOURCE_FIRST"`)
  - Allowed: `"SOURCE_FIRST"`, `"OFFSET_ASC"`, `"ALPHABETICAL"`

#### `logging` (optional)

- `level` (string, optional, default: `"INFO"`)
  - Allowed: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`
- Validation is implementation-specific; not part of core/adapter contract.

### Validation Notes

- Invalid numeric values → default is used with warning.
- Invalid IANA timezone → treated as `null` (UTC fallback) with warning.
- Invalid YAML → `yaml.YAMLError` is raised and adapter fails to start.
- Full type/range validation rules: see `ADAPTER_CONTRACTS.md` §5.

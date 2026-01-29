# Future Work

Details: `ARCHITECTURE.md` §5, `USER_PROFILE_MODEL.md` §8, `STORAGE_MODEL.md`.

---

## Near-term (Optional / Future)

- Extend parser with additional time formats (per `TIME_PARSING_RULES.md`).
- Extend timezone resolution (e.g. multi-segment IANA, Etc/GMT+X per `TIMEZONE_EXTRACTION_RULES.md`).
- (Optional) Define explicit ambiguity rules or thresholds (current: no reply on ambiguity, `POLICIES.md` §4).

## Mid-term (Optional / Future)

- Add persistent storage for user/channel context.
- Introduce a simple adapter interface for platforms.

## Long-term (Optional / Future)

- Additional platform adapters (Discord, WhatsApp).
- Multilingual parsing and advanced date expressions.

---
node_id: concorda-api::services/error_alerts.py::record_exception
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 83dfbc4f84fc45c2b2e9703050000fa2042a2176479f74c551c895486b4c5d78
status: current
---

# record_exception

## Purpose

Captures and surfaces unhandled exceptions and high-severity status codes to the admin alert pipeline. It is used to transform a standard Python exception or a notable HTTP status (like a 429 or 500) into a structured, fingerprinted alert. Use `record_exception` for true 5xx errors and `record_status` for non-exception events like rate limits or unauthenticated attempts.

## Invariants

- **Always calls `_record_and_maybe_notify`** to ensure the error is passed to the central alerting logic.
- **`traceback_text` is a string.** If `tb_mod.format_exception` fails, it falls back to `repr(exc)` to ensure a string is always provided for the alert payload.
- **`status_code` is hardcoded to 500** when called via `record_exception`.
- **`path` is a required string** used for fingerprinting and deduplication in the alert pipeline.

## Gotchas

- **Fingerprinting logic is sensitive to `path` composition.** Per `record_email_failure`, the `path` must encode both `event_type` and `template_name` to ensure alerts deduplicate at the template level rather than the recipient level.
- **The alert pipeline uses a fingerprint-cooldown mechanism.** If you change how `path` or `error_class` is passed, you may inadvertently change the frequency of alerts sent to admins.

## Cross-cutting concerns

- **Auth**: Uses `person_uuid` and `attempted_user` to provide context for unauthenticated or failed authentication attempts.
- **Audit**: Writes a log row via `_record_and_maybe_notify` (and `logger.warning` in the event of a failure) to track system-wide errors.
- **Side effects**: Triggers the admin alert pipeline for 5xx errors, 429 rate limits, and email transport failures.

## External consumers

None known. (Internal to `concorda-api` service layer).

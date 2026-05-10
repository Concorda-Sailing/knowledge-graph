---
node_id: concorda-api::services/error_alerts.py::record_status
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9272f4ecccea15ed73cc9aa8d33b696849cdb56a233e5dbc4d73bb8a9ed6fd45
status: llm_drafted
---

# record_status

## Purpose

Captures non-exception status events (like rate limits or unauthenticated attempts) to trigger administrative alerts. Unlike `record_email_failure`, which is specialized for template and transport errors, `record_status` is a generic sink for high-level HTTP-style status codes. Use this when you need to track "soft" failures (e.g., 429s or 401s) that do not involve a Python exception but still require visibility in the alert pipeline.

## Invariants

- **`error_class` is `None`** — This method is designed for non-exception events, so it does not accept or generate an error class.
- **`detail` maps to `error_message`** — The `detail` argument is passed directly to the internal `_record_and_maybe_notify` call as the error message.
- **`attempted_user` is the primary identifier for unauthenticated paths** — Use this field to capture the identity (e.g., email) of a user during a failed login attempt.
- **`path` must be a valid URI string** — The path is used for grouping and fingerprinting in the downstream alert system.

## Gotchas

- **Fingerprinting relies on `path` and `method`** — Per the logic in the sibling `record_email_failure`, the alert pipeline groups by these fields; if you use generic paths for different types of failures, you may inadvertently deduplicate/suppress distinct alerts.
- **`attempted_user` is critical for login-related monitoring** — As noted in the docstring, this is the only way to track "who" was trying to act during unauthenticated requests (e.g., a specific email during a 401/429 event).

## Cross-cutting concerns

- **Auth**: Used to track failed authentication attempts via `attempted_user`.
- **Rate limit**: Specifically used to surface 429 status codes to admins.
- **Audit**: Triggers the fingerprint-cooldown alert pipeline via `_record_and_maybe_notify`.

## External consumers

None known.

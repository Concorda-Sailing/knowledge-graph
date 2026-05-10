---
node_id: concorda-api::services/error_alerts.py::record_email_failure
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: baad0840b7427e720e79bdd7db4c73e8678f777d8985706dabefe8fe9e2e60d5
status: llm_drafted
---

# record_email_failure

## Purpose

Captures and surfaces failures occurring during the email dispatch process (e.g., template rendering errors, missing template rows, or transport failures from SendGrid/Mailgun/SMTP). It wraps the error into a standardized alert via `_record_and_maybe_notify`. Use this instead of generic error logging when an email failure is a business-critical event that requires immediate admin visibility via the fingerprint-cooldown pipeline.

## Invariants

- **Hardcoded status code** — Always calls `_record_and_maybe_notify` with `status_code=500`.
- **Method is always "EMAIL"** — The method identifier is fixed to allow the alert pipeline to distinguish transport/render errors from standard HTTP 5xx errors.
- **Path-based deduplication** — The `path` is constructed as `email:{event_type}:{template_name}`. This ensures that errors are fingerprinted by the specific template/event type rather than the recipient, preventing a single failing template from flooding alerts for every user.
- **Traceback extraction** — If an exception (`exc`) is provided, the function attempts to extract the class name, message, and a stringified traceback.

## Gotchas

- **Deduplication logic** — Because the `path` encodes the `template_name`, a single broken template will trigger a single alert fingerprint. If you change the `template_name` or `event_type` in a call, you are effectively creating a new alert stream.
- **Traceback fallback** — If `tb_mod.format_exception` fails, the function falls back to `repr(exc)`. This is a safety measure to ensure the alert is still recorded even if the traceback extraction itself crashes.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: Y (writes to the error/alert pipeline)
- **Rate limit**: Subject to the fingerprint-cooldown logic in `_record_and_maybe_notify`.
- **Side effects**: Triggers admin notifications via the error-alert pipeline (used for 5xx and 429 monitoring).

## External consumers

None known.

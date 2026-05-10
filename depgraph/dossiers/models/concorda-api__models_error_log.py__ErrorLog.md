---
node_id: concorda-api::models/error_log.py::ErrorLog
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b4fbc4dd957c29d51f798b594c7ad0a5dc117bd1986a92568171b8422f7738ec
status: current
---

# ErrorLog

## Purpose

The `ErrorLog` model captures 5xx server exceptions and 429 rate-limiting events to drive the admin alert pipeline. It is distinct from standard application logging as it is designed for structured storage and coalescing; the `fingerprint` field allows the system to group identical errors to prevent alert fatigue during a cooldown window.

## Invariants

- **`fingerprint` is mandatory.** It is a 64-character string used to coalesce identical errors.
- **`status_code` is an integer.** It tracks the specific HTTP error (e.g., 500 or 429).
- **`person_uuid` is optional.** It tracks the specific user identity associated with the error, if available.
- **`notified_at` is a nullable DateTime.** This tracks when the alert was actually dispatched to admins.

## Gotchas

- **Coalescing logic depends on `fingerprint`.** Per commit `da1589d`, the error-alert pipeline uses this field to implement "structured login lockouts" and prevent redundant notifications. If a new error type is added without a unique fingerprinting strategy, it may trigger duplicate alerts.

## Cross-cutting concerns

- **Auth**: Accessed via `GET /api/admin/error-log`, which is protected by admin-level authorization.
- **Audit**: Acts as the primary sink for 5xx and 429 error telemetry.
- **Side effects**: Drives the admin alert pipeline (email/notifications) via the `fingerprint` cooldown logic.

## External consumers

- Admin dashboard (via `GET /api/admin/error-log`).

---
node_id: POST::/api/auth/forgot-password
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3cd6fe5e0f4464f9c58fd6c68777c7d40b69db709087b38c50279d9b761875a9
status: current
---

# POST /api/auth/forgot-password

## Purpose

Triggers a password reset flow by generating a unique token and sending a reset email to the user. It is designed to be side-effect-free regarding user enumeration; it returns a success message regardless of whether the email exists in the database to prevent account discovery attacks.

## Invariants

- **Returns a success message regardless of email existence** to prevent leaking user presence.
- **Input email is normalized** via `.strip().lower()` to ensure case-insensitive matching with the `Person` record.
- **Invalidates existing tokens** by setting `used = True` on any existing unused `PasswordResetToken` for the user before creating a new one.
- **Uses `_rate_limit_lock`** to manage the IP-based request window.

## Gotchas

- **Test environment bypasses real email delivery** by echoing the `reset_token` in the response. This is a deliberate feature for E2E testing (see commit `3582125`).
- **Rate limiting is skipped in test environments** via the `_RATE_LIMITS_DISABLED` flag.
- **Email failures are caught and logged** to the `NotificationLog` with `status="failed"` and the error string, but the exception is re-raised to ensure the client receives a 500 error if the service-level failure is critical.
- **Case-sensitivity matters for lookups.** Per commit `9a5db8f`, the email lookup must use `func.lower(Person.email)` to match the case-insensitive login/register behavior.

## Cross-cutting concerns

- **Auth**: Triggers the `PasswordResetToken` lifecycle.
- **Rate limit**: Throttled by IP address via `_reset_rate_limit` and `_RESET_RATE_LIMIT_MAX`.
- **Audit**: Writes to `NotificationLog` for both successful (`status="sent"`) and failed (`status="failed"`) email attempts.
- **Side effects**: Triggers `record_email_failure` in `services.error_alerts` if the email dispatch fails.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.forgotPassword`
- `concorda-web::src/lib/api.ts::authApi.forgotPassword`

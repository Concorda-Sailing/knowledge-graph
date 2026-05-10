---
node_id: POST::/api/admin/email-config/test
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 345a480aa04e18359c28c0cf92d1501526608300e9ee3838487872c5d9bf0209
status: llm_drafted
---

# POST /api/admin/email-config/test

## Purpose

Provides a mechanism for administrators to verify that the SMTP configuration is functional by sending a hardcoded test email. It serves as a diagnostic tool to ensure the server can successfully hand off emails to the configured provider before a user attempts to configure complex production settings.

## Invariants

- **Requires `require_auth`** — The request must be authenticated.
- **Requires `_require_system_admin`** — Only users with system administrator privileges can trigger this endpoint.
- **Hardcoded content** — The subject is always `"MBSA - Test Email"` and the body is a fixed HTML template.
- **Returns a success message** — On success, returns `{"message": "Test email sent successfully"}`.
- **Error handling** - If `send_email` fails, it raises a 500 Internal Server Error with a specific detail string.

## Gotchas

- **Security gate dependency** - Per commit `650233f`, this endpoint is part of the admin-only surface area; ensure any changes do not bypass the `_require_system_admin` check, which prevents privilege escalation.
- **Environment-specific behavior** - The `send_bulk_email` logic (sibling) shows that rate-limiting is skipped if `CONCORDA_ENV` is `"test"`, but this specific test endpoint does not have an explicit rate-limit guard in its own body, relying instead on the `_require_system_admin` check.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `_require_system_admin` privileges.
- **Audit**: `ActivityMiddleware` (referenced in sibling `send_bulk_email`) records hits to admin endpoints for incident review.
- **Side effects**: Success confirms the connectivity of the organization's email-config settings.

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailConfigApi.sendTestEmail`

---
node_id: PUT::/api/admin/email-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c25e316559870e4fdda969a960a836af4f885bba83a21e98ed6f1f5f22b806f5
status: current
---

# PUT /api/admin/email-config

## Purpose

Updates the global email configuration settings (SMTP, SendGrid, or Mailgun) for the organization. This endpoint is used by the admin dashboard to manage the credentials and endpoints required for the system to send automated notifications and event-related emails.

## Invariants

- **HTTP Method:** `PUT`.
- **Auth Requirement:** Requires a valid session via `require_auth`.
- **Authorization Guard:** Only users with `_require_system_admin` privileges can access this endpoint.
- **Return Shape:** Returns an `EmailConfigResponse` containing the updated configuration.
- **Secret Protection:** Values starting with `"..."` (e.g., `"...masked"`) are treated as placeholders and will not overwrite existing secrets in the database.

## Gotchas

- **Secret Masking Logic:** The loop in `update_email_config` explicitly checks `isinstance(value, str) and value.startswith("...")` to prevent accidental overwriting of sensitive API keys with placeholder strings during partial updates.
- **Admin Privilege Escalation:** Per commit `650233f`, this endpoint and its surrounding admin routes are subject to strict privilege checks to prevent non-admin users from modifying system-level configurations.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_require_system_admin`.
- **Rate limit**: Indirectly related to `_BULK_EMAIL_RATE_LIMIT_MAX` (5) and `_BULK_EMAIL_MAX_RECIPIENTS` (2000) defined in the same module, which govern the consumption of these credentials.
- **Side effects**: Changes to these settings directly impact the success or failure of `send_email` calls used in event notifications and system alerts.

## External consumers

- `concorda-web` (via `adminEmailConfigApi.update`)

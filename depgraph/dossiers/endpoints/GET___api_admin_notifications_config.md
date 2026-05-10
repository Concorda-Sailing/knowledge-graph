---
node_id: GET::/api/admin/notifications/config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4d145b1f0dadaa14dbab8880520f59b5804af6edd155e5830ff1ab096e8a59e3
status: llm_drafted
---

# GET /api/admin/notifications/config

## Purpose

Retrieves the current notification configuration settings, specifically for Twilio (SMS/WhatsApp) integration. This is a read-only view of the system-wide notification state. It is distinct from the `PUT` method in that it returns masked secrets to ensure sensitive credentials are not exposed in plain text to the client.

## Invariants

- **HTTP Method is `GET`**.
- **Requires `system_admin` role** via the `_require_admin` guard.
- **Returns `NotificationConfigResponse`**.
- **Secrets are masked** — `twilio_account_sid` and `twilio_auth_token` are passed through `_mask_secret` before being returned.
- **Returns empty config if none exists** — if the database query returns no record, an empty `NotificationConfigResponse` is returned rather than a 404.

## Gotchas

- **Masking is mandatory for security** — the `_mask_secret` function is used to prevent leaking the full Twilio credentials to the frontend.
- **Role dependency** — access is strictly gated by `_require_admin`. If a user has a valid session but lacks the `system_admin` role, they will receive a 403.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `system_admin` role via `_require_admin`.
- **Audit**: N/A.
- **Side effects**: N/A.

## External consumers

- `concorda-web` (via `adminNotificationConfigApi.get`)

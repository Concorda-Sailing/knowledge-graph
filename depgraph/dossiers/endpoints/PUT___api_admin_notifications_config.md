---
node_id: PUT::/api/admin/notifications/config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 90233a92f730960197bc5fe47b62d295ffbf0a565ed48aa2071da885eb654a1c
status: current
---

# PUT /api/admin/notifications/config

## Purpose

Updates the global notification settings for the organization, specifically managing Twilio credentials and toggle states for SMS and WhatsApp. It acts as a single-row configuration manager that either updates the existing `NotificationConfig` or initializes a new one if none exists. Use this endpoint when an administrator needs to rotate Twilio secrets or toggle communication channels.

## Invariants

- **Method is `PUT`** — used for full or partial updates to the configuration object.
- **Requires `_require_admin(current_user)`** — only users with administrative privileges can access or modify these settings.
- **Returns `NotificationConfigResponse`** — the response includes masked versions of sensitive fields via `_mask_secret`.
- **Partial updates via `exclude_unset=True`** — only the fields provided in the request body are updated; omitted fields retain their current values in the database.
- **Automatic initialization** — if no `NotificationConfig` record exists in the database, a new one is created and committed.

## Gotchas

- **Secret protection logic** — the loop prevents overwriting existing secrets with masked strings. If a client attempts to send a value starting with `"..."` (the mask pattern), the `setattr` call is skipped for that key. This prevents the API from accidentally persisting the string `"...[masked]..."` into the database.
- **`updated_at` timestamp** — every call to this endpoint updates the `updated_at` field to `datetime.utcnow()`, ensuring the configuration's freshness is tracked.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_require_admin`.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to this config immediately affect the behavior of `send_sms` and `send_whatsapp` calls throughout the system.

## External consumers

- `concorda-web::src/lib/api.ts::adminNotificationConfigApi.update` (via `api.ts:1004`).

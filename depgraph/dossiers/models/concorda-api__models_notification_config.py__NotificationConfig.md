---
node_id: concorda-api::models/notification_config.py::NotificationConfig
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3d7afaa4d7c2531d765de31373df174ff2baa4322c571c631b3e6a71dbcc5fb2
status: current
---

# NotificationConfig

## Purpose

The singleton configuration model for SMS and WhatsApp notification channels. It stores the credentials and toggle states for Twilio-based messaging. Use this model when you need to access or update the global notification settings for the platform, rather than user-specific notification preferences.

## Invariants

- **Single instance pattern** — The `__init__` method forces the `type` to be `"NotificationConfig"`, ensuring this behaves as a singleton within the `BaseModel` hierarchy.
- **String-based toggles** — `sms_enabled` and `whatsapp_enabled` use `"on"` and `"off"` strings rather than booleans.
- **Twilio credentials** — `twilio_account_sid` and `twilio_auth_token` are the required credentials for any outbound SMS/WhatsApp logic.
- **Nullable fields** — Most fields (except the `type` in `__init__`) are nullable to allow for partial updates or uninitialized states.

## Gotchas

- **String-based boolean logic** — Per the source, `sms_enabled` and `whatsapp_enabled` default to `"off"` and expect `"on"`/`"off"` strings. Passing a boolean `True/False` from a client might cause unexpected behavior or type errors in the DB layer if not handled by the serializer.
- **Recent schema reorganization** — Commit `7ee3ad5` added these notification endpoints and schema documentation; ensure any new notification logic references this model rather than hardcoding Twilio credentials in the service layer.

## Cross-cutting concerns

- **Auth**: Managed via `GET /api/admin/notifications/config` and `PUT /api/admin/notifications/config`. Access is restricted to admin-level permissions.
- **Audit**: Updates to this model via the `PUT` endpoint should be monitored, as it changes the global state of how the system communicates with users.

## External consumers

- None known. (Internal to `concorda-api` and used by the admin notification endpoints).

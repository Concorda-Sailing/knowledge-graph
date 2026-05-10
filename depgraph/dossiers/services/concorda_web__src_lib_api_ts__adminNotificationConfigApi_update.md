---
node_id: concorda-web::src/lib/api.ts::adminNotificationConfigApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 392c1670c798f3a1f5a9b927fbda2cc78967dc1c197b0f4b118b990bf78bdd0c
status: current
---

# adminNotificationConfigApi.update

## Purpose

Updates the global administrative notification settings, specifically for SMS and WhatsApp connectivity. It is used by the admin dashboard to modify the configuration of how the system broadcasts alerts. This method is distinct from the `testSMS` and `testWhatsApp` methods, which are used for ephemeral testing of connectivity rather than persisting configuration changes.

## Invariants

- **Method is `PUT`** — Uses `fetchApiAuthenticated` with the `PUT` method to update the existing configuration.
- **Input is a `Partial<NotificationConfigData>`** — Allows for updating only specific fields (like `sms_enabled` or `twilio_phone_number`) without providing the full object.
- **Returns `NotificationConfigData`** — The response body is the full, updated configuration object.
- **Requires Admin Authentication** — Relies on `fetchApiAuthenticated` to ensure the caller has the necessary permissions to modify system-wide notification settings.

## Gotchas

- **Configuration vs. Testing** — Ensure you are using `update` for persistent changes to the `twilio_phone_number` or `whatsapp_enabled` flags. Using the `testSMS` or `testWhatsApp` methods will not persist any changes to the system configuration.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level credentials).
- **Side effects**: Updates to this configuration may affect how automated alerts are dispatched via Twilio or WhatsApp services.

## External consumers

- `SMSConfigPage` in `concorda-web/src/app/members/admin/sms/page.tsx`
- `WhatsAppConfigPage` in `concorda-web/src/app/members/admin/whatsapp/page.tsx`

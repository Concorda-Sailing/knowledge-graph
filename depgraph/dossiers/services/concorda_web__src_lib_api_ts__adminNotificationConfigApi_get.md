---
node_id: concorda-web::src/lib/api.ts::adminNotificationConfigApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a88f41d0c4db65635fa4bbeca7c4fc3eb50d39e7d0e2d0da94c1756e98de21d
status: llm_drafted
---

# adminNotificationConfigApi.get

## Purpose

Provides access to the administrative configuration for external notification services (Twilio and WhatsApp). It allows administrators to view current notification settings and perform test transmissions to verify connectivity and configuration integrity. Use `get` to retrieve the current state and `testSMS` or `testWhatsApp` to validate specific phone number connectivity.

## Invariants

- **Uses `fetchApiAuthenticated`** — all calls require a valid administrative session.
- **`get` returns `NotificationConfigData`** — includes status for `sms_enabled` and `whatsapp_enabled` alongside provider credentials.
- **`update` accepts `Partial<NotificationConfigData>`** — allows updating specific fields (like `sms_enabled`) without sending the full object.
- **`testSMS` and `testWhatsApp` return `{ message: string }`** — the response body is a simple confirmation string.

## Gotchas

- **Credential sensitivity** — the `get` method returns sensitive fields like `twilio_auth_token` and `twilio_account_sid`. Ensure any UI component consuming this data masks these values and does not leak them to non-admin logs.
- **Manual verification required** — while the API provides `testSMS` and `testWhatsApp`, these are used to verify the connection between the server and the provider, not to verify the user's ability to receive messages (which depends on local device settings).

## Cross-cutting concerns

- **Auth**: Requires administrative privileges via `fetchApiAuthenticated`.
- **Side effects**: Successful calls to `testSMS` or `testWhatsApp` trigger external outbound messages via Twilio/WhatsApp providers.

## External consumers

- `SMSConfigPage` (via `page.tsx:26`)
- `WhatsAppConfigPage` (via `page.tsx:26`)

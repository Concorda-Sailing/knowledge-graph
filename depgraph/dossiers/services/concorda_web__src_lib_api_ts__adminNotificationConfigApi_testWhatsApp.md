---
node_id: concorda-web::src/lib/api.ts::adminNotificationConfigApi.testWhatsApp
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6a88712070f438b9489e15160c379eee8ab82a67e7acf9d87a2d36e52c46e206
status: current
---

# adminNotificationConfigApi.testWhatsApp

## Purpose

Provides a method to trigger a test WhatsApp message to a specific phone number. This is used by administrators to verify that the notification configuration and the WhatsApp provider integration are functioning correctly before deploying new settings. It is distinct from `testSMS` by targeting the WhatsApp messaging channel.

## Invariants

- **HTTP Method is `POST`** — The endpoint requires a POST request to initiate the test.
- **Requires `fetchApiAuthenticated`** — The call must include a valid administrative bearer token.
- **Input parameters** — Accepts `to_phone` (string) and an optional `message` (string).
- **Return shape** — Returns a promise resolving to an object with a `message` property (e.g., `{ message: string }`).

## Gotchas

- **Admin-only access** — Because this uses `fetchApiAuthenticated`, the caller must have administrative privileges; failure to do so will result in a 401 or 403 error depending on the backend implementation.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Triggers an external WhatsApp provider API call to send a message.

## External consumers

- `WhatsAppConfigPage` in `concorda-web/src/app/members/admin/whatsapp/page.tsx`.

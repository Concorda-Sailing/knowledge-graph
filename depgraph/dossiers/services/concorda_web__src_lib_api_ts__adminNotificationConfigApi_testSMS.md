---
node_id: concorda-web::src/lib/api.ts::adminNotificationConfigApi.testSMS
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d1366c604c2882e4e8f4daf02160637a45ca2c03a5c029882f285d5802eb4f17
status: llm_drafted
---

# adminNotificationConfigApi.testSMS

## Purpose

The `testSMS` method provides a diagnostic endpoint for administrators to verify that the SMS notification pipeline is functional. It triggers a single SMS message to a specified phone number with an optional message body. This is distinct from the `update` method, which modifies the persistent notification configuration; `testSMS` is a transient, side-effect-driven tool for testing connectivity.

## Invariants

- **Method is `POST`** — The request must use the POST method to trigger the SMS dispatch.
- **Requires `to_phone`** — The `to_phone` parameter is a required string.
- **Returns a message object** — The successful response shape is `{ message: string }`.
- **Uses `fetchApiAuthenticated`** — The call is wrapped in the authenticated fetch helper, requiring a valid admin session.

## Gotchas

- **Requires valid phone format** — While the type is `string`, the underlying service expects a format compatible with the SMS provider (e.g., E.164).
- **Side effects on SMS provider** — Frequent calls to this method will consume actual SMS credits and may trigger rate-limiting at the provider level, even if the local API doesn't explicitly throttle it.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires an active admin session.
- **Side effects**: Triggers an external SMS delivery.

## External consumers

- `SMSConfigPage` in `src/app/members/admin/sms/page.tsx`.

---
node_id: concorda-api::models/notification_log.py::NotificationLog
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1c58182c94168cc91d99b61acdf4a8799dc44a57196fc093ac2784b81487ed77
status: current
---

# NotificationLog

## Purpose

The `NotificationLog` model serves as the immutable record for all outbound communications (SMS, WhatsApp, Email) sent via the system. It tracks the lifecycle of a message from initial dispatch to delivery or failure, providing a debugging trail for both the system and the end-user. Use this model when you need to audit why a user did or did not receive a critical alert (e.g., a crew invite or a password reset).

## Invariants

- **`person_uuid` is mandatory** and indexed to allow fast lookups of a user's communication history.
- **`channel` must be one of `sms`, `whatsapp`, or `email`** to ensure compatibility with downstream provider logic.
- **`tracking_token` is a unique 36-character string** used to identify specific events (like email opens) without exposing the user's identity directly in the URL.
- **`status` defaults to `"sent"`** and tracks the progression through `delivered` or `failed`.
- **`to_address` is the destination identifier**, which may be a phone number for SMS/WhatsApp or an email address for email.

## Gotchas

- **`tracking_token` is the primary key for tracking-related GET requests.** As seen in `GET::/api/tracking/email-open/{0}`, the system relies on this token to link an external interaction (like an email click) back to a specific log entry.
- **`error` field is a text blob.** When a notification fails, the full traceback or provider error message is stored here to prevent loss of debugging context during transient API failures.

## Cross-cutting concerns

- **Auth**: Indirectly used by `POST /api/auth/forgot-password` to verify the delivery of reset instructions.
- **Audit**: Every entry represents a single audit event for outbound communication.
- **Side effects**: Successful/failed notifications directly impact the reliability of the "Crew Invite" system and the "Forgot Password" flow.

## External consumers

- `GET /api/tracking/email-open/{0}` (Email tracking endpoint).
- `POST /api/auth/forgot-password` (Auth flow dependency).

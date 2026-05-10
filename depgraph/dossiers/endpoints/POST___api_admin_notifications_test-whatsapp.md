---
node_id: POST::/api/admin/notifications/test-whatsapp
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3d4005e0ab7b24d6a49ffe691799bfe3a095138346bce48b899d50711fa48281
status: llm_drafted
---

# POST /api/admin/notifications/test-whatsapp

## Purpose

Triggers a test WhatsApp message to verify the Twilio/WhatsApp integration is functioning correctly. This is a diagnostic tool used by admins to ensure the messaging pipeline is active before relying on it for production notifications. It is distinct from the SMS test endpoint, as it uses the `send_whatsapp` logic path.

## Invariants

- **Requires Admin privileges** — The call is guarded by `_require_admin(current_user)`.
- **Input schema** — Expects a `TestWhatsAppRequest` containing `to_phone` and `message`.
- **Returns success object** — On success, returns `{"message": "Test WhatsApp message sent"}`.
- **Throws 500 on failure** — If the underlying `send_whatsapp` call fails, it raises an `HTTPException` with a detail regarding configuration.

## Gotchas

- **Configuration dependency** — Failure is almost always a configuration issue (e.g., Twilio credentials or WhatsApp sandbox settings) rather than a code bug.
- **`event_type="test"`** — The function hardcodes the event type to `"test"`, ensuring these diagnostic messages do not trigger standard production notification workflows or billing logic.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and specifically `_require_admin`.
- **Audit**: N/A.
- **Side effects**: None known.

## External consumers

- `concorda-web::src/lib/api.ts::adminNotificationConfigApi.testWhatsApp`

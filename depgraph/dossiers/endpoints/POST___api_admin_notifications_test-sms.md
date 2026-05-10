---
node_id: POST::/api/admin/notifications/test-sms
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 500bb472eee0c3fdd295874606f958172b47ccde56b3790c9d6d674566464730
status: llm_drafted
---

# POST /api/admin/notifications/test-sms

## Purpose

Provides a diagnostic tool for administrators to verify the Twilio SMS integration. It allows a user to send a single-message test to a specific phone number to ensure the `twilio_phone_number` and `sms_enabled` configuration settings are correctly propagated and functional. This is distinct from the standard notification flow as it uses a hardcoded `event_type="test"`.

## Invariants

- **Method is `POST`**.
- **Requires `current_user` with admin privileges** via the `_require_admin` guard.
- **Input must be a `TestSMSRequest`** containing `to_phone` and `message`.
- **Returns a 200 OK** with `{"message": "Test SMS sent"}` on success.
- **Throws a 500 error** if the underlying `send_sms` call fails, specifically citing Twilio configuration issues.

## Gotchas

- **Relocation of logic:** Per commit `ef1c3bd`, root-level helpers were relocated to `utils/` and `scripts/`. Ensure any manual testing of this endpoint accounts for the fact that the underlying `send_sms` logic is no longer in the local router scope.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes the `_require_admin` check.
- **Audit**: The `send_sms` call tracks the `person_uuid` of the `current_user` as the sender.
- **Rate limit**: None explicitly defined, but relies on the stability of the Twilio provider configuration.

## External consumers

- `concorda-web` via `adminNotificationConfigApi.testSMS`.

## Open questions

- Should this endpoint also support a "test WhatsApp" variant to allow admins to verify the WhatsApp-specific configuration through the same interface? (Currently, `test-whatsapp` is a separate endpoint).

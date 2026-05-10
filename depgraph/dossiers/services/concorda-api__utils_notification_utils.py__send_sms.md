---
node_id: concorda-api::utils/notification_utils.py::send_sms
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d1d378b3e5accaf10041cf1e550abdab49231dbaeaeea165b09de72b8fe0bcf
status: current
---

# send_sms

## Purpose

Sends SMS messages via the Twilio API to a specified phone number. It acts as a high-level wrapper that handles configuration retrieval, Twilio client instantiation, and automated logging of success or failure states. Use this instead of `send_whatsapp` when the communication channel must be standard SMS.

## Invariants

- **Returns a boolean.** Returns `True` if the message was successfully handed off to Twilio, and `False` if the service is disabled, configuration is missing, or an exception occurred.
- **Requires a valid `db` session.** The function relies on `get_notification_config(db)` to fetch credentials and the `_log` function to record the transmission attempt.
- **Uses `NotificationConfig` for credentials.** The `_get_twilio_client` helper requires `twilio_account_sid` and `twilio_auth_token` to be present in the config object.
- **Logs all outcomes.** Every attempt (success or failure) triggers a call to `_log` with the `channel="sms"` identifier.

## Gotchas

- **SMS is disabled by default if `sms_enabled` is not `"on"`.** If the configuration is missing or the flag is set differently, the function returns `False` and prints a `[SMS-disabled]` message to stdout rather than attempting a send.
- **Missing Twilio credentials result in silent failure.** If `twilio_account_sid` or `twilio_auth_token` are missing, `_get_twilio_client` returns `None`, and the function exits with a `[SMS-no-client]` log.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: Y (Writes to the audit log via `_log` with `channel="sms"` and includes `message.sid` on success).
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

- `POST /api/admin/notifications/test-sms` (via `routers/notifications.py`)

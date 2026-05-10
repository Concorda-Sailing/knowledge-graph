---
node_id: concorda-api::utils/notification_utils.py::send_whatsapp
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 16e3cc2cfbac0550d63bbf17f2b401852c885de074fc0ec7dd98ff4b36cda235
status: current
---

# send_whatsapp

## Purpose

Sends a WhatsApp message via the Twilio API. It is a specialized sibling to `send_sms`, used when the user's notification preferences explicitly include "whatsapp". It handles the Twilio client initialization and provides a fallback log entry if the message fails to send.

## Invariants

- **Requires an active configuration.** The function returns `False` immediately if `config.whatsapp_enabled` is not `"on"` or if `config.whatsapp_phone_number` is missing.
- **Input `to_phone` must be a string.** The function prepends the `whatsapp:` prefix to both the sender and receiver identifiers before calling the Twilio client.
- **Returns a boolean.** Returns `True` on successful API response and `False` on any exception or configuration failure.
- **Logs to the database.** Every attempt (success or failure) triggers a call to `_log` with `channel="whatsapp"`.

## Gotchas

- **Silent failure on disabled config.** If the WhatsApp toggle is off, it prints to stdout (`[WhatsApp-disabled]`) and returns `False` rather than raising an error, which can lead to silent failures in high-level flows if the caller doesn't check the return value.
- **Dependency on `get_notification_config`.** If the database session `db` is not properly initialized or the config is missing, the function fails gracefully but the notification is lost.

## Cross-cutting concerns

- **Auth**: None (relies on `_get_twilio_client` and internal config).
- **Websocket**: None.
- **Audit**: Writes a log row via `_log` for both success and failure states.
- **Rate limit**: None.
- **Side effects**: Used by `notify_person` to dispatch messages based on user preferences.

## External consumers

- `POST /api/admin/notifications/test-whatsapp` (via `routers/notifications.py`).

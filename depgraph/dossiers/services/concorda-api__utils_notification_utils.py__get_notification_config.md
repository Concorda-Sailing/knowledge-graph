---
node_id: concorda-api::utils/notification_utils.py::get_notification_config
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fc5530dbfb94368c9f818fd601ffce2f3ed749319f053ee1d5df1f4bd610d6cc
status: llm_drafted
---

# get_notification_config

## Purpose

Retrieves the singleton `NotificationConfig` record from the database. This function serves as the foundational provider for all outbound communication services (SMS, WhatsApp, Email) within the `notification_utils` module. It ensures that the `send_sms` and `send_whatsapp` functions have access to the necessary Twilio credentials and enabled/disabled status flags.

## Invariants

- **Returns a single record.** It queries the `NotificationConfig` table and returns the first available record or `None`.
- **Requires a SQLAlchemy `Session`.** The function is a direct dependent of the `db` session passed from the caller.
- **Provides the source of truth for credentials.** The `twilio_account_sid` and `twilio_auth_token` retrieved here are used by `_get_twilio_client` to instantiate the Twilio client.

## Gotchas

- **Single-record assumption.** The function uses `.first()`, assuming only one configuration exists in the database. If the system ever requires multi-tenant configuration support, this method will only ever return the first one found, regardless of the context.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: Indirectly used by `_log` via `send_sms` and `send_whatsapp` to track delivery status.
- **Rate limit**: None.
- **Side effects**: Provides the configuration state that controls whether `send_sms` and `send_whatsapp` execute or fall back to a print statement (e.g., `[SMS-disabled]`).

## External consumers

None known.

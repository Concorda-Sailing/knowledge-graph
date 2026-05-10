---
node_id: concorda-api::utils/notification_utils.py::notify_person
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae82aa4742fa5606da87cc32dbf9be1c353953f956580e9d8a19c812d120c3ad
status: current
---

# notify_person

## Purpose

The primary dispatcher for multi-channel notifications (SMS, WhatsApp, and Email) to a `Person`. It resolves the user's preferred communication channels from their `preferences` object and executes the corresponding delivery logic. Use this instead of calling `send_email` or `send_whatsapp` directly when the notification target is a `Person` entity, as it ensures the system respects individual user settings and fallback logic.

## Invariants

- **Returns a `dict[str, bool]`** mapping the channel name (e.g., `"email"`, `"sms"`) to a success/failure boolean.
- **Defaults to `"email"`** if the `notifications.channels` key is missing or empty in the user's preferences.
- **Requires a `Person` object** with a valid `id` and the necessary contact fields (`email` or `phone_number`) populated for the requested channels.
- **The `db` session must be passed through** to ensure that `_log` calls and downstream service calls (like `send_email`) can participate in the same transaction or logging context.

## Gotchas

- **The alert pipeline must be non-blocking.** Per the implementation of `record_email_failure`, the `try/except` block around the error alert service ensures that a failure in the error-reporting mechanism itself does not crash the primary request path.
- **`html_body` is a fallback for `body`.** If `html_body` is not provided, the function wraps the raw `body` in `<p>` tags to ensure valid HTML delivery for email clients.
- **`subject` is required for professional-looking emails.** While it defaults to `"Notification"`, failing to pass a subject results in generic headers in the user's inbox.

## Cross-cutting concerns

- **Auth**: none.
- **Websocket**: none.
- **Audit**: Writes to the database via `_log` for every attempt (sent or failed) across all channels.
- **Rate limit**: none.
- **Side effects**: Triggers `record_email_failure` in `services.error_alerts` if the email delivery attempt throws an exception.

## External consumers

- Internal to `concorda-api` (used by invitation and event-driven workflows).

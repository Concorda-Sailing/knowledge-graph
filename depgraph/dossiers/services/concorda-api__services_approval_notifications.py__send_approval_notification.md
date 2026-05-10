---
node_id: concorda-api::services/approval_notifications.py::send_approval_notification
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 571ee2e8acaebab6165721a19fbe840aa57fdfb11d646eec04cf7c76de1a2837
status: current
---

# send_approval_notification

## Purpose

Dispatches multi-channel notifications (in-app, email, and push) triggered by approval requests. It acts as the central orchestrator for notifying users of pending actions, such as co-owner invites or general approvals, by rendering a template and logging the attempt to the database.

## Invariants

- **Always logs to `NotificationLog`** — Every attempt (success or failure) is recorded in the database to ensure a persistent audit trail of notifications.
- **`person_uuid` is the primary key** — The function relies on a valid `person_uuid` to fetch the user's email and identity; if the user is not found, the function exits silently.
- **Email routing is type-dependent** — Uses `_send_email_html_for_invite` for `boat_coowner_invite` requests and `_send_approval_html_email` for all other types.
- **Push is "best effort"** — The `_send_push` helper is wrapped in a try-except block and is designed to fail silently without interrupting the email or in-app notification flow.

## Gotchas

- **Email failure logging is recursive/fragile** — If an email fails, it attempts to call `record_email_failure` from `services.error_alerts`. If this secondary service fails or the import is broken, the error is swallowed by a bare `except Exception: pass`.
- **Template dependency** — Per commit `8f84d2d`, the renderer is hardened to handle templated event notifications. If the `template_key` or the `request` object structure changes, the `_render` call will fail, potentially breaking the entire notification chain.
- **Import-based push fallback** — The `_send_push` function uses a local import of `send_push` from `utils.notification_utils`. If this utility is missing or the import fails, the function catches the `ImportError` and returns `None` without error.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: Y (Writes to `NotificationLog` for both `in_app` and `email` channels).
- **Rate limit**: none
- **Side effects**: Triggers the delivery of "Accept/Decline" links in emails (per commit `8f96045`).

## External consumers

None known.

## Open questions

- The `_send_push` implementation relies on a fragile local import; should this be moved to a standard dependency injection or a more robust service-level import to avoid `ImportError` at runtime?

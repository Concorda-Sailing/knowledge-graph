---
node_id: concorda-api::utils/email_utils.py::send_coowner_status_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 842b5c609efbfad4c69509e0f4cf78d1595fa7415f6595e4fab25782efcc6ccf
status: llm_drafted
---

# send_coowner_status_email

## Purpose

Sends status update emails to co-owners regarding boat ownership changes (invites, acceptances, expirations, etc.). It wraps the `render_email_template` logic to ensure that all co-owner lifecycle events use a consistent context and the correct managed templates. Use this instead of `send_email` directly when a co-owner status change occurs to ensure the `template_key` and `ctx` (context) are correctly formatted.

## Invariants

- **`template_key` must be one of the seven allowed strings** defined in the docstring (`coowner_invite_created`, `coowner_invite_accepted`, `coowner_invite_welcome`, `coowner_invite_declined`, `coowner_invite_expired`, `coowner_invite_expired_target`, or `coowner_invite_canceled`).
- **`db` session must be passed** to allow the template renderer to access necessary organization or boat metadata.
- **`to_email` must be a valid string**; the function does not validate email format before attempting to pass it to `send_email`.
- **`boat_id` is required** to build the context for the template.

## Gotchas

- **Timezone-aware body content:** Per commit `6c314f5`, ensure that any datetime data passed into the context for these emails is rendered in the organization's timezone, not UTC, to avoid confusion in the email body.
- **Template dependency:** This function is a consumer of `render_email_template`. If the signature of the renderer changes, this function will break.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Triggers user-facing notifications for boat crew/co-owner lifecycle changes.

## External consumers

None known.

---
node_id: concorda-api::utils/email_utils.py::send_support_request_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a259071ac75775470a57e1a6eddc47105c5e8c6bcbd51dcc2fe7cbc0d31548b
status: current
---

# send_support_request_email

## Purpose

Sends a templated help-request email from a member to the MBSA support inbox. It constructs an HTML body containing the sender's name, phone, and message, and sets the `Reply-To` header to the sender's email address to facilitate direct communication. Use this specifically for support-related requests; for event-related notifications (invites, logistics, etc.), use the `CREW_EMAIL_KINDS` pattern instead.

## Invariants

- **`Reply-To` is the `sender_email`** — This ensures that when the support team hits "Reply" in their email client, the response goes to the user, not the system's automated `SUPPORT_EMAIL`.
- **Input strings are HTML-escaped** — `sender_name`, `sender_email`, and `message` are passed through `html.escape` to prevent injection or rendering errors in the email body.
- **`support_email` resolution order** — The recipient is determined by `SUPPORT_EMAIL` env var, then `config.get("support_email")`, then `config.get("from_email")`, defaulting to `membership@massbaysailing.org`.

## Gotchas

- **Template rendering requires `db`** — The function calls `render_email_template`, which requires an active database session to fetch configuration or template data.
- **HTML line breaks** — The `message` content is escaped and then has `\n` replaced with `<br>` to ensure the message preserves visual structure in the HTML email body.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers an external SMTP/email delivery via `send_email`.

## External consumers

- `POST /api/support/request-help` (via `routers/support.py:46`).

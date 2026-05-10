---
node_id: concorda-api::utils/email_utils.py::send_password_reset_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a9a3d3914e4131b1f4957ba355b70dbd8eb6f6d758078934c7102f26c8f402e7
status: current
---

# send_password_reset_email

## Purpose

Generates and sends a password reset email containing a secure, single-use token. It retrieves the base URL from the system configuration to construct the `reset_url` and uses the `password_reset` template to render the body. Use this method specifically for the "forgot password" flow; for other transactional emails like crew applications or contact proxies, use the specialized sibling functions in this module.

## Invariants

- **Requires a valid `db: Session`** to fetch the current email configuration and base URL.
- **Constructs a `reset_url`** by appending the `token` as a query parameter to the `web_base_url` found in `get_email_config`.
- **Uses `html.escape`** on the `first_name` parameter to prevent XSS in the email body.
- **Relies on `render_email_template`** to produce the final `subject` and `html_body`.

## Gotchas

- **Template dependency:** This function is a direct consumer of the `password_reset` template. If the template structure changes (e.g., variable names), this function will fail during the `render_email_template` call.
- **URL construction:** The `reset_url` is built using `config['web_base_url']`. If the configuration is missing the trailing slash or has an incorrect protocol, the resulting link in the email will be malformed.

## Cross-cutting concerns

- **Auth**: Triggered by the `POST /api/auth/forgot-password` endpoint.
- **Audit**: N/A.
- **Side effects**: None known.

## External consumers

- `POST /api/auth/forgot-password` (via `routers/auth.py`).

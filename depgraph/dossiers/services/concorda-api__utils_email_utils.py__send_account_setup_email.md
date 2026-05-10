---
node_id: concorda-api::utils/email_utils.py::send_account_setup_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f4d3eba3645b0b7dcdfa6ee902ae9de7f94f6aa4ffef35c28a63a9e2addb10f0
status: llm_drafted
---

# send_account_setup_email

## Purpose

Generates and sends the initial account setup email containing a secure token and a deep-link to the account setup page. This is a specialized wrapper around `render_email_template` and `send_email` specifically for the onboarding flow. Use this instead of `send_email_verification` when the user is being invited/onboarded, as it targets the `account_setup` template rather than standard email verification.

## Invariants

- **Requires a valid `token`** — This token is used to construct the `setup_url` via the `web_base_url` found in the email config.
- **Uses `account_setup` template** — The function explicitly renders the `account_setup` template name.
- **Dependency on `get_email_config(db)`** — The `web_base_url` (used for the setup link) is pulled from the database configuration.
- **Input types** — `to_email` must be a string, `first_name` is used for template personalization, and `token` is the unique identifier for the setup session.

## Gotchas

- **Template hardening** — Per commit `8f94d2d`, all user-facing emails must use the managed templates and ensure `first_name_html` is escaped via `html.escape` to prevent injection in the email body.
- **URL construction** — The `setup_url` is built using `config['web_base_url']`. If the configuration is misconfigured or the base URL is missing, the link in the email will be broken or point to an incorrect domain.

## Cross-cutting concerns

- **Auth**: Indirectly related to the auth flow; provides the token used for the `/setup-account` endpoint.
- **Audit**: N/A.
- **Side effects**: Triggers the account setup flow for new users.

## External consumers

- `POST /api/auth/resend-setup-email` (via `routers/auth.py:1024`).

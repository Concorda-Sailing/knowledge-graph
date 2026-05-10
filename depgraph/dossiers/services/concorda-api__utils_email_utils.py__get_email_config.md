---
node_id: concorda-api::utils/email_utils.py::get_email_config
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1ddb7ad2711c02cd6b884d373b6b38abe3d8090e0229f6d28d569e51feb63a92
status: current
---

# get_email_config

## Purpose

Retrieves the configuration required for sending emails, prioritizing settings stored in the database via the `EmailConfig` model. It provides a fallback mechanism to environment variables to ensure the system can function in local development or CI environments without a database connection. Use this to ensure that `smtp_host`, `mode`, and `web_base_url` are consistent across the application.

## Invariants

- **Returns a `dict`** containing keys for `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `from_email`, `from_name`, `support_email`, `sendgrid_api_key`, `mailgun_api_key`, `mailgun_domain`, `mode`, and `web_base_url`.
- **`web_base_url` is always stripped** of trailing slashes to prevent double-slashes when appending paths in email templates.
- **`smtp_port` is cast to an `int`** when using the environment variable fallback.
- **`mode` defaults to `"console"`** in the environment fallback, allowing developers to see email output in stdout rather than attempting to hit a real SMTP server.

## Gotchas

- **`web_base_url` fallback value:** The hardcoded fallback in the environment return is `"http://felix:6401"`. If an agent changes the default `WEB_BASE_URL` in the environment, they must ensure it remains a valid URL for the local dev stack.
- **Hardcoded fallback name:** The default `from_name` is `"MBSA"`. If the organization rebrands, this string is a common source of "stale branding" bugs in local development.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Affects the construction of all user-facing emails, including `event_crew` notifications and `invite` links.

## External consumers

- Internal to `concorda-api/utils/email_utils.py` (used by `send_email` and `send_email_verification`).

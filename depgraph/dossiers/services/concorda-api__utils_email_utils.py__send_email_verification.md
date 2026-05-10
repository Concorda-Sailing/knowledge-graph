---
node_id: concorda-api::utils/email_utils.py::send_email_verification
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fdc4d2037426d9d838e3b11bba2022bff6f09c34e04c0211e3b08e7f0ea6ee6
status: current
---

# send_email_verification

## Purpose

Generates and dispatches the email verification link during the user registration flow. It constructs a signed URL using the organization's base URL and a provided token, then renders the `email_verification` template via `render_email_template`. This is a specialized helper within `email_utils.py` used specifically for identity confirmation, distinct from the password reset or crew-finder flows.

## Invariants

- **Requires a valid `db` Session** to fetch configuration via `get_email_config`.
- **Constructs a signed `verify_url`** by appending the `token` to the `web_base_url` path `/verify-email?token=`.
- **Uses `html.escape` on `first_name`** to prevent XSS in the rendered HTML body.
- **Relies on `render_email_template`** to handle the actual string interpolation and template loading.

## Gotchas

- **Template dependency:** This function relies on the existence of the `"email_verification"` template string in the template engine. If the template name is changed or removed, registration will fail.
- **URL construction:** The `verify_url` is built using `config['web_base_url']`. If the configuration is missing the trailing slash or has an incorrect base, the verification link will be malformed.

## Cross-cutting concerns

- **Auth**: Directly triggered by `POST /api/auth/register` (via `routers/auth.py:834`).
- **Side effects**: Successful execution of this function is a prerequisite for a user to move from a "pending" to an "active" state in the authentication lifecycle.

## External consumers

- `POST /api/auth/register` (via `routers/auth.py`).

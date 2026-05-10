---
node_id: GET::/api/admin/email-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4a18189b1c7524f7a03b908635def540493082a36072f69b3b92fba4131d4994
status: llm_drafted
---

# GET /api/admin/email-config

## Purpose

Retrieves the current SMTP and third-party email provider configuration (SendGrid/Mailgun). This is a read-only view of the `EmailConfig` model used to populate the admin settings dashboard. It is distinct from the `PUT` endpoint which handles updates, and the `POST /test` endpoint which triggers a single-use verification email.

## Invariants

- **Auth requirement**: Requires a valid session via `require_auth`.
- **Authorization**: Access is strictly restricted to users with system admin privileges via `_require_system_admin`.
- **Response shape**: Returns an `EmailConfigResponse` object.
- **Secret masking**: Sensitive fields (SMTP password, API keys) are passed through `_mask_secret` before being returned to the client to prevent accidental exposure in logs or UI.
- **Default state**: If no configuration exists in the database, the endpoint returns a hardcoded set of defaults (e.g., `smtp.gmail.com`, `mode="console"`, and `web_base_url="http://felix:6401"`).

## Gotchas

- **Secret preservation**: When updating via the sibling `PUT` endpoint, the logic explicitly checks for `...` prefixes to avoid overwriting existing secrets with masked placeholders (see `update_email_config` logic).
- **Default URL dependency**: The default `web_base_url` is set to `http://felix:6401`. If the frontend or test environment relies on this for generating absolute URLs (e.g., in email templates), it must be updated to a public-facing URL.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_require_system_admin`.
- **Side effects**: Changes to this configuration (via the `PUT` sibling) directly impact the success/failure of the `send_email` function used by the event-driven notification system.

## External consumers

- `concorda-web` (via `adminEmailConfigApi.get`).

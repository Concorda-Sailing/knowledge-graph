---
node_id: concorda-api::models/email_config.py::EmailConfig
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e078e693f75b6802bcab1f118c7ae9d5e2993570246c77a6f363cedb48681523
status: llm_drafted
---

# EmailConfig

## Purpose

The `EmailConfig` model acts as a singleton configuration store for all outbound communication settings. It manages credentials and endpoints for multiple providers (SMTP, SendGrid, and Mailgun) to ensure the system can switch between local development and production-grade delivery. Use this model when you need to resolve the `web_base_url` for generating absolute links in emails or when determining which provider to use based on the current `mode`.

## Invariants

- **Singleton pattern** — Only one row is expected to exist in the `email_config` table; queries should typically use `.first()`.
- **`mode` is required** — The `mode` field (defaulting to `"console"`) dictates the operational context of the API.
- **`web_base_url` is mandatory** — This field must be populated to ensure absolute URLs in email templates (e.g., for password resets or event invites) function correctly.
- **`updated_at` auto-updates** — The timestamp is automatically refreshed on every update via `datetime.utcnow`.

## Gotchas

- **Multi-provider support** — Per commit `a7a8a37`, the model was expanded to support both `sendgrid_api_key` and `mailgun_api_key`. Ensure that adding a new provider doesn't break existing logic that might rely on a single provider's presence.
- **Default `web_base_url` is local** — The default value `"http://felix:6401"` is a local development hostname. If this is not updated in a staging or production environment, all absolute links in outgoing emails will fail to resolve for external users.

## Cross-cutting concerns

- **Auth**: Managed via the `/api/admin/` router; requires administrative privileges to modify.
- **Side effects**: Changes to this model directly affect the construction of absolute URLs in all system-generated emails (e.g., boat-share invites, calendar invites).

## External consumers

- N/A — Internal to `concorda-api`.

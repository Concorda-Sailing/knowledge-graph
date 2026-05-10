---
node_id: concorda-web::src/app/members/admin/email/page.tsx::AdminEmailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6fea2b7016a406b1e4a53c16daefd232ea168b1631b9bf943276fd0380ca1983
status: llm_drafted
---

# AdminEmailPage

## Purpose

Provides the administrative interface for configuring the application's email delivery settings. It allows administrators to manage SMTP credentials, API keys for third-party providers (SendGrid/Mailgun), and the default "from" address/name. It is distinct from a standard user profile or notification settings, as it controls the global-level identity and transport layer for the entire organization.

## Invariants

- **Initial state is hardcoded** — The `config` state initializes with a default `mode: "console"` and a local `web_base_url` of `http://felix:6401`.
- **Requires `adminEmailConfigApi`** — All state updates and test email triggers must go through this specific API utility to ensure the backend receives the correct payload shape.
- **`handleSave` is an atomic update** — It replaces the entire `EmailConfigData` object on the server.
- **Test email requires a recipient** — The `handleSendTest` function returns early if `testEmail` is an empty string.

## Gotchas

- **Configuration is global, not per-user** — Changes made here affect all outgoing system emails (e.g., invites, alerts) immediately.
- **Manual fallback for local development** — The default `web_base_url` is set to `http://felix:6401`. If the local environment is not configured with this specific host, links in outgoing emails may fail to resolve correctly.

## Cross-cutting concerns

- **Auth**: Relies on administrative-level permissions (implied by the path `/members/admin/`).
- **Side effects**: Updating the `from_email` or `from_name` affects the branding of all system-generated emails, including crew invites and boat-share notifications.

## External consumers

- None known. (Configuration is consumed by the backend mailer service, not the frontend).

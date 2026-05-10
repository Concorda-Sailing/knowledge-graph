---
node_id: concorda-web::src/lib/api.ts::adminEmailConfigApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 436d1bf2e1e7724307730298bfd557130e6ef7430d9ac5d2dc3de0d82776ee10
status: llm_drafted
---

# adminEmailConfigApi.get

## Purpose

Fetches the current Mailgun configuration for the organization. This includes the domain, sender name, and support email addresses used for automated communications. It is the primary source of truth for the Admin Email Configuration page, ensuring that the `from_email` and `web_base_url` used in system-generated emails are consistent with the current settings.

## Invariants

- **Returns `EmailConfigData`** — the object contains `mailgun_domain`, `from_email`, `from_name`, `support_email`, `mode`, and `web_base_url`.
- **Requires authentication** — calls `fetchApiAuthenticated` and will fail if a valid bearer token is not present.
- **Read-only via this method** — this specific method is a `GET` request; use `adminEmailConfigApi.update` for modifications.

## Gotchas

- **Configuration dependency** — the `web_base_url` returned here is critical for constructing absolute links in emails; if this is misconfigured, links in system-generated emails (like invites) will point to the wrong domain.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level credentials).
- **Side effects**: Changes to the configuration via the sibling `update` method affect the identity and link-generation of all system-sent emails.

## External consumers

- `AdminEmailPage` in `src/app/members/admin/email/page.tsx`.

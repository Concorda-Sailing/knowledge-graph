---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2557761b4e3eb382d1159283cec7788c1862829ccd0704df9e70bce63b46a9c6
status: current
---

# adminEmailTemplatesApi.list

## Purpose

Provides the administrative interface for managing email templates used by the system. It allows for listing, creating, updating, and deleting templates, as well as previewing a template's rendered content. Use this specific object when you need to manage the structural components (subject, body, variables) of system-generated emails, rather than the notification configuration itself.

## Invariants

- **Requires authentication** — all methods call `fetchApiAuthenticated`.
- **Returns `EmailTemplate` objects** — the `list` and `get` methods return arrays or single instances of the `EmailTemplate` interface.
- **`preview` uses POST** — the `preview(id)` method must be called with a `POST` method to the `/preview` endpoint to render the template with current context.
- **Variables are typed** — the `variables()` method returns `EmailTemplateVariable[]` to ensure the UI can display the expected keys and example values.

## Gotchas

- **Previewing requires a POST request** — unlike the `get` method which retrieves the template structure, `preview` hits a specific `/preview` endpoint via `POST` to simulate the rendered output.
- **Template variables are dynamic** — the `variables` method is critical for the UI to know which `key` strings to inject into the `body` to avoid broken templates.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: Changes to templates via `create`, `update`, or `delete` will immediately affect the content of any system emails sent to users (e.g., invite emails or status updates).

## External consumers

- `EmailTemplatesPage` (Admin dashboard)
- `ComposeEmailPage` (Admin dashboard)

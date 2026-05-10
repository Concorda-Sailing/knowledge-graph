---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c600979b2b3ebafcf9681fac16d20c6afdce41e90bb00d53ab3b546c2674db64
status: current
---

# adminEmailTemplatesApi.get

## Purpose

Provides a programmatic interface for managing the lifecycle of administrative email templates. This includes retrieving specific templates, previewing rendered bodies, and managing the list of available variables. Use this when building admin UI components that require dynamic content injection or when managing the system's automated communication templates.

## Invariants

- **Requires `fetchApiAuthenticated`** — All methods rely on an authenticated session to access the `/api/admin/` namespace.
- **`get(id)` returns a single `EmailTemplate` object.**
- **`preview(id)` uses a `POST` method.** This is a side-effect-free simulation of the template rendering to allow admins to see how variables resolve without actually sending an email.
- **`variables()` returns an array of `EmailTemplateVariable`.** This is used to populate the UI with the expected keys (e.g., `{{user_name}}`) available for a specific template.

## Gotchas

- **Template variable mismatch:** While the API provides a `variables` endpoint, the `body` of a template is a raw string. If a developer introduces a new variable in the template body but fails to update the `variables` list or the backend logic, the preview may fail or show empty strings.
- **`is_active` flag dependency:** When updating a template via `update`, ensure the `is_active` boolean is explicitly handled if the UI intends to toggle the template's availability for automated triggers.

## Cross-cutting concerns

- **Auth**: Requires admin-level privileges via `fetchApiAuthenticated`.
- **Audit**: N/A.
- **Side effects**: Changes to templates via `update` or `delete` will immediately affect the content of any automated system emails (e.g., invites, status updates) sent to users.

## External consumers

None known.

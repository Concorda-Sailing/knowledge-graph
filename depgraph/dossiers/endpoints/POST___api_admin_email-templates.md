---
node_id: POST::/api/admin/email-templates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3a66bd1efd163b2d39295df2ea243b0a9421f53802ec56f38ee2875cb64bdf29
status: llm_drafted
---

# POST /api/admin/email-templates

## Purpose

Provides the administrative interface for managing the structure and content of email templates. This endpoint allows for the creation, updating, and deletion of templates used by the system to send automated notifications (e.g., event crew notifications). It is distinct from the template *rendering* logic, which is a separate concern handled by the frontend and the `_example_value_for` utility.

## Invariants

- **POST `/email-templates`** requires a unique `name`; if a name collision occurs, it returns a `409 Conflict`.
- **PUT `/email-templates/{template_id}`** uses `exclude_unset=True` for partial updates, allowing for granular field updates without overwriting the entire object.
- **DELETE `/email-templates/{template_id}`** returns a simple JSON message `{"message": "Template deleted"}` upon success.
- **Response models** are strictly typed to `EmailTemplateRead` to ensure the frontend receives a consistent object shape.

## Gotchas

- **Template Variable Synthesis:** The `_example_value_for` helper is used to prevent layout collapse during preview. It uses specific suffixes like `_url` or `_block` to generate plausible-looking data. If you change the naming convention for variables, you must update this helper to avoid broken previews.
- **Security/Privilege Escalation:** Per commit `65023 возможный escalation`, ensure any new admin-level endpoints added to this router are strictly guarded to prevent unauthorized access to template structures.
- **HTML Escaping:** The system relies on `html_lib.escape` for certain variable types (like `_html` or `dock_time_html`) to ensure that placeholder text doesn't break the layout or introduce XSS during the preview phase.

## Cross-cutting concerns

- **Auth**: Admin-level access required (implied by the `/admin/` path and recent security fixes in `650233f`).
- **Rate limit**: Subject to general admin endpoint protections.
- **Side effects**: Changes to templates directly affect the visual output of automated notifications (e.g., `event_crew` notifications) sent via the background worker.

## External consumers

- `concorda-web` (specifically `adminEmailTemplatesApi.create`)

## Open questions

- Should the `_example_value_for` logic be moved to a shared utility or a separate service to allow the mobile/Expo client to use the same preview logic without importing the Python-specific logic?

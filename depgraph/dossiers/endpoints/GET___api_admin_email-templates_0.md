---
node_id: GET::/api/admin/email-templates/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c2d97756e93b47e6fef9fbe71f24b2f5f89ef9fb8053d8f8e4f842f432a23e01
status: current
---

# GET /api/admin/email-templates/{template_id}

## Purpose

Retrieves a single email template by its unique identifier. This endpoint is used by the admin dashboard to allow administrators to preview and inspect specific notification layouts (e.g., event crew notifications) before deploying changes. It is distinct from the list endpoint, which returns all templates, and is the primary way to fetch the full `EmailTemplateRead` object for a specific template.

## Invariants

- **Returns `EmailTemplateRead`** — the response includes the template name, the raw template body, and any variable definitions.
- **Requires a `template_id`** — the path parameter must be a valid string matching a template in the database.
- **Throws 404 on missing ID** — if the `template_id` does not exist, the API raises an `HTTPException` with the detail `"Template not found"`.
- **Ordering is handled by the list sibling** — while this fetches one, the sibling `list_email_templates` orders by `EmailTemplate.name`.

## Gotchas

- **Template variable synthesis** — per `_example_value_for`, the system uses suffix-based logic to generate mock data for previews. If a template variable ends in `_html`, the system escapes the value to prevent layout collapse during preview (see `html_lib.escape` usage in `_example_value_for`).
- **Admin-only access** — while the source shows the logic, the `admin` prefix in the route implies this is protected by admin-level middleware/guards elsewhere in the router stack.

## Cross-cutting concerns

- **Auth**: Requires admin-level privileges (implied by the `/api/admin/` path).
- **Side effects**: Changes to templates via the sibling `POST/PUT` methods will immediately affect the rendering of system-generated emails (e.g., event crew notifications).

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailTemplatesApi.get` (used for admin dashboard previews).

## Open questions

- The `_example_value_for` helper is used for "synthesizing plausible example values" for previews; it is unclear if this logic should eventually be moved to a dedicated service or if it remains a purely internal utility for the template-rendering preview.

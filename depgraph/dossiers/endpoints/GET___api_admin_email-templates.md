---
node_id: GET::/api/admin/email-templates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 041a04a73b2880af455b77612ae2614e036558adbf1dd2ed0d328c5f3b99c67f
status: current
---

# GET /api/admin/email-templates

## Purpose

Provides a read-only list of all configured email templates for the organization. This endpoint is used by the admin dashboard to allow administrators to review and manage the branding and structure of automated communications (e.g., event notifications, registration confirmations). It is distinct from `/api/admin/email-templates/variables`, which returns the specific keys and example values available for use within those templates.

## Invariants

- **Returns a list of `EmailTemplateRead` objects.** Each object contains the template's unique ID, name, and content.
- **Ordering is alphabetical by name.** The query uses `.order_by(EmailTemplate.name)` to ensure a consistent UI experience in the admin dashboard.
- **Requires a database session.** The endpoint depends on `get_db` for fetching the template records from the `EmailTemplate` table.

## Gotchas

- **Admin-only access.** While the source shows a standard `get_db` dependency, the router is part of the `admin` namespace; ensure any changes to the schema or return model do not break the admin dashboard's ability to render the list.
- **Template variable synthesis.** The helper `_example_value_for` (used for the sibling `/variables` endpoint) relies on specific string suffixes like `_url` or `_block` to generate safe preview data. If a template variable name does not follow these conventions, the preview might render broken layouts or unescaped strings.

## Cross-cutting concerns

- **Auth**: Admin-level access required (part of the `admin` router).
- **Side effects**: Changes to the underlying `EmailTemplate` model (via POST/PUT/DELETE) will affect the rendering of automated emails across the system, such as `event_crew` notifications.

## External consumers

- `concorda-web` (via `adminEmailTemplatesApi.list`)

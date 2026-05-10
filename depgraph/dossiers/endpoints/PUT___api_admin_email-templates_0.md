---
node_id: PUT::/api/admin/email-templates/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d6ef3e9f32165aac5352d03462e7e902844595af3d1d57dc9aa87fecfc9317db
status: llm_drafted
---

# PUT /api/admin/email-templates/{template_id}

## Purpose

Updates an existing email template's configuration. This endpoint allows for partial updates to an `EmailTemplate` via the `EmailTemplateUpdate` model. It is distinct from the `POST` endpoint (which creates new templates) and the `POST .../preview` endpoint (which simulates rendering without persisting changes).

## Invariants

- **Method is `PUT`** and requires a `template_id` in the path.
- **Partial updates via `exclude_unset=True`** — only fields explicitly provided in the request body are updated on the existing database record.
- **Returns `EmailTemplateRead`** — the response is the fully updated object, including server-side fields.
- **Requires a valid `Session`** via the `get_db` dependency.

## Gotchas

- **Template name collisions** — while this is a `PUT` (update), the `POST` logic in the same file (see line 1394) enforces that names must be unique. If an update logic were to change to allow name-swapping, it would trigger the `409` error defined in the sibling `POST` method.
- **`_example_value_for` dependency** — the preview functionality (which relies on the same data structures) uses a suffix-based heuristic to synthesize data (e.g., `_html` or `_url`). Changes to the template schema must remain compatible with these hardcoded string-parsing rules to avoid breaking the preview UI.

## Cross-cutting concerns

- **Auth**: Requires admin-level privileges (implied by the `/admin/` path and `get_db` dependency).
- **Side effects**: Updates to templates directly affect the output of the `preview_email_template` endpoint and any production email-sending services that consume these templates.

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailTemplatesApi.update`

## Open questions

- The `_example_value_for` logic is highly brittle and relies on string suffixes (e.g., `_html`, `_url`). Should this be formalized into a typed schema or a registry to prevent the preview tool from breaking when new variable types are added?

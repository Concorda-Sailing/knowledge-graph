---
node_id: GET::/api/admin/email-templates/variables
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7c4610207e3b236af163326c912dfd49d01692fcb192d6e5173e0a0236dcf24f
status: current
---

# GET /api/admin/email-templates/variables

## Purpose

Returns the available variables and their metadata for use in the email template editor. This endpoint provides the labels and example values used to populate the preview UI, allowing admins to see how a template will look with real-world data before saving. It is distinct from the template CRUD endpoints as it returns static/synthesized metadata rather than specific template instances.

## Invariants

- **Returns a dictionary of template variables.** The response shape is driven by the `EMAIL_TEMPLATE_VARIABLES` constant.
- **Synthesizes example values.** If a variable is not explicitly provided in the `variables` dict, the system uses `_example_value_for` to generate a plausible string (e.g., "Jane" for `first_name` or a URL for `_url` suffixes) to prevent layout collapse during preview.
- **Static response.** This endpoint does not take any arguments and does not interact with the database.

## Gotchas

- **Preview fallback logic.** The function `_example_value_for` is critical for the "preview" experience; if a new variable is added to the system but not accounted for in the suffix-matching logic (like `_url` or `_block`), the preview might render empty or broken layouts.
- **Hardcoded suffixes.** The logic in `_example_value_for` relies on string suffixes (e.g., `_url`, `_block`) to determine the type of example data to inject.

## Cross-cutting concerns

- **Auth**: Admin-level access required (part of the `/api/admin` router).
- **Side effects**: Changes to the variable list or the synthesis logic in `_example_value_for` will immediately change the visual output of the email template preview in the web UI.

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailTemplatesApi.variables`

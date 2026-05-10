---
node_id: POST::/api/admin/email-templates/{0}/preview
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 656fc14d6243cef6a75b4cc255fceb6ddc907b7f9111bffaf3f0c13e0e1a8786
status: current
---

# POST /api/admin/email-templates/{template_id}/preview

## Purpose

Generates a preview of an email template by rendering it with a set of example variables. It is used by administrators to verify how a template looks before it is sent to real users. Unlike a standard fetch, this endpoint executes the full `render_email_template` logic—including `app_title` injection and regex-based substitution—to ensure the preview matches the production rendering behavior exactly.

## Invariants

- **Method is POST.**
- **Returns `EmailTemplatePreview`.** The response contains the rendered `subject`, the rendered `body`, and a list of `unresolved_variables`.
- **`template_id` is required.** Must be a valid UUID/string corresponding to an existing `EmailTemplate`.
- **`overrides` is optional.** If provided, the `variables` object in the request body replaces the default example values for the rendering context.
- **Throws 404 if template is missing.**
- **Throws 400 if rendering fails.** Specifically if a `ValueError` is raised during the `render_email_template` call (e.g., due to missing or invalid variable-related logic).

## Gotchas

- **Regex-based detection.** The endpoint uses `_PLACEHOLDER_RE` to find leftover `{{var}}` patterns in the subject and body. This is the primary way admins detect broken or unfulfilled templates before deployment.
- **Requires `render_email_template` parity.** Because this uses the actual production rendering path, any change to `utils.email_utils` (like the `app_title` or `support_email` injection) will immediately change the output of this preview.
- **Admin-only access.** While not explicitly shown in the snippet, the surrounding context of `admin.py` and the `_admin` only observability section suggests this is a privileged endpoint.

## Cross-cutting concerns

- **Auth**: Requires admin-level authorization (implied by the `admin.py` router context).
- **Side effects**: None. This is a read-only preview and does not trigger actual email dispatch.

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailTemplatesApi.preview`

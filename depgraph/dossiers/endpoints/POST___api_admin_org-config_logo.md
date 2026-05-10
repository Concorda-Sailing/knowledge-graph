---
node_id: POST::/api/admin/org-config/logo
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 34686159df4480d49a108d65138797dce28a16cafcee058e4d89edf91f52476d
status: llm_drafted
---

# POST /api/admin/org-config/logo

## Purpose

Uploads and persists the organization's branding logo. It handles the file storage via `save_upload` and triggers a side-effect to regenerate the site's favicon. This is distinct from the `DELETE` method in the same router, which is used to clear the existing logo and file reference.

## Invariants

- **Requires `_require_system_admin`** — only users with system administrator privileges can access this endpoint.
- **Returns `OrgConfigResponse`** — the response body contains the updated `OrgConfig` object, including the new `logo_url`.
- **Triggers `_generate_favicon_from_logo`** — an upload automatically attempts to create a `favicon.ico` from the new image.
- **Uses `save_upload` with specific pathing** — the file is saved using the `"logo"` and `"org"` identifiers to ensure correct directory placement.

## Gotchas

- **Argument order sensitivity** — commit `3d3b23b` fixed a bug where the `save_upload` arguments were in the wrong order; ensure the order remains `(file, "logo", "org")` to avoid pathing errors.
- **Non-critical failure mode** — the `_generate_favicon_from_logo` function uses a broad `try/except` block. If the `PIL` (Pillow) library fails or the `logo_path` is missing, the function returns silently rather than raising an error, ensuring the logo upload succeeds even if the favicon generation fails.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and specifically passes the `_require_system_admin` check.
- **Side effects**: Triggers the generation of `favicon.ico` in the `UPLOAD_DIR`.

## External consumers

None known.

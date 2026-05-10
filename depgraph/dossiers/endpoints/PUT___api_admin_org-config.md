---
node_id: PUT::/api/admin/org-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 950ea3519a2c670625b57dc4ee053c47469c3767ddcc7fffdf92c09defa1ee46
status: current
---

# PUT /api/admin/org-config

## Purpose

Updates the global organization configuration settings. This endpoint allows system administrators to modify high-level metadata like the organization name and the email address used for error notifications. It is distinct from the `/org-config/logo` endpoint, which handles media assets and favicon generation.

## Invariants

- **Requires `_require_system_admin`** — Only users with system-level privileges can modify these settings.
- **Returns `OrgConfigResponse`** — The response shape is a serialized version of the `OrgConfig` model.
- **`error_notify_email` handling** — An empty string `""` in the input is converted to `None` to disable email alerts.
- **`exclude_unset=True`** — Only the fields explicitly provided in the request body are updated; omitted fields remain unchanged in the database.

## Gotchas

- **Logo upload argument order** — Per commit `3d3b23b`, ensure any logic interacting with `save_upload` in the sibling `/org-config/logo` endpoint respects the correct argument order to avoid runtime errors.
- **Favicon generation is non-critical** — The `_generate_favicon_from_logo` function uses a broad `except Exception: pass` block. If the PIL/Pillow processing fails, the logo upload still succeeds, but the favicon may not be updated.
- **Email notification disabling** — To disable error alerts, the client must send an empty string `""` for `error_notify_email`. Sending a null/missing field may not trigger the `None` conversion depending on the client's JSON serialization.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and `_require_system_admin` (system admin role).
- **Side effects**: Updating the logo triggers `_generate_favicon_from_logo`, which attempts to create a `favicon.ico` in the `UPLOAD_DIR`.

## External consumers

- `concorda-web` (via `adminOrgConfigApi.update`)

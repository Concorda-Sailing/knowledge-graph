---
node_id: DELETE::/api/admin/org-config/logo
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f24462e6e10b6f8674bc0a3a9912b2a68e7f314ae1662bd20bf02528fb94d7b0
status: llm_drafted
---

# DELETE /api/admin/org-config/logo

## Purpose

Removes the organization's logo from the filesystem and resets the configuration. It calls `delete_upload` to handle the physical file removal and updates the `OrgConfig` record to ensure the `logo_url` is null. This is used by the admin dashboard to clear branding-related assets.

## Invariants

- **HTTP Method is `DELETE`**.
- **Requires `_require_system_admin` authorization**.
- **Returns `OrgConfigResponse`**. If no configuration exists, it returns a default object with `logo_url=None`.
- **Mutates `config.logo_url` to `None`** in the database before committing.

## Gotchas

- **Argument order sensitivity**: A recent fix in commit `3d3b23b` corrected the `save_upload` argument order in related org-logo endpoints; ensure any logic involving the hand-off between the API and the storage layer maintains this corrected order to avoid signature mismatches.
- **Non-critical failure handling**: The logo removal process (specifically the favicon generation logic seen in the surrounding context) is wrapped in a broad `except Exception: pass` block. A failure in the secondary asset generation/cleanup should not prevent the primary `logo_url` from being cleared.

## Cross-cutting concerns

- **Auth**: Requires `_require_system_admin` via `require_auth`.
- **Side effects**: Triggers the removal of physical files via `delete_upload("logo", "org")`.

## External consumers

- `concorda-web::src/lib/api.ts::adminOrgConfigApi.deleteLogo`

---
node_id: PUT::/api/media/folders/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0467aa3e76965d3f1feca76e9ab50d2b07dce3216df593c554e03dd9c1b097e8
status: current
---

# PUT /api/media/folders/{folder_id}

## Purpose

Updates the metadata of an existing media folder, such as its name or visibility scope. This is the primary way to rename or re-scope folders in the media management UI. It is distinct from the creation endpoint, which handles initial setup and ownership assignment.

## Invariants

- **Method is `PUT`** and requires a valid `folder_id` in the path.
- **Requires `AuthUser`** via the `require_auth` dependency.
- **Returns `FolderRead`** shape on success.
- **`scope` validation is mandatory.** The `update_data` must contain a scope present in `VALID_SCOPES` (e.g., `private`, `crew`, `public`).
- **Ownership check is strict.** A user can only update a folder if they are the `owner_uuid` or hold `system_admin` or `org_admin` roles.

## Gotchas

- **IDOR Vulnerability:** Per commit `c9a7c41`, the endpoint requires strict ownership/role checks to prevent users from modifying folders they do not own.
- **Scope mismatch:** If the `scope` provided in the payload is not in `VALID_SCOPES`, the API returns a 400 error (see logic in line 223).
- **Database Session Management:** Per commit `3fee226`, ensure any logic involving `FileResponse` or streaming related to these paths releases the DB session to avoid hanging connections.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and checks for `system_admin` or `org_admin` roles to bypass ownership requirements.
- **Audit**: N/A.
- **Side effects**: Changes to folder scope or name may affect how files within these folders are indexed or displayed in the media browser.

## External consumers

- `concorda-web::src/lib/api.ts::mediaApi.updateFolder`

---
node_id: DELETE::/api/media/folders/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e7d1ba0c9ac3d6bde2c8152333517f4ed8297d75213534f98eeb7605f98e8bbc
status: current
---

# DELETE /api/media/folders/{folder_id}

## Purpose

Deletes a media folder from the database. This endpoint is used to clean up the media hierarchy, but it is strictly constrained to prevent accidental data loss or orphaned files. Unlike the `PUT` endpoint which allows updating folder metadata, this is a terminal operation that requires the folder to be empty.

## Invariants

- **HTTP Method/Path**: `DELETE /api/media/folders/{folder_id}`.
- **Auth Requirement**: Requires `require_auth`.
- **Permission Logic**: Only the `owner_uuid` of the folder or a user with `system_admin` or `org_admin` roles can delete the folder.
- **Non-empty Guard**: The operation fails with a `400` error if the folder contains any `MediaFile` children or any subfolders.
- **Return Status**: Returns a `204 No Content` on successful deletion.

## Gotchas

- **Strict Empty Check**: The endpoint performs a count on both `MediaFile` and `MediaFolder` (lines 244-247). If a folder contains even one file, the deletion is blocked with a `400` error.
- **IDOR Protection**: Per commit `c9a7c41` (security: tier-A IDOR audit fixes), the permission check (lines 241-243) is critical. A user cannot delete a folder they do not own, even if they know the `folder_id`.
- **Role-based Access**: The `is_admin` check allows `system_admin` or `org_admin` to bypass the ownership requirement, which is essential for support-level interventions.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` and checks for `system_admin` or `org_admin` roles.
- **Audit**: N/A.
- **Side effects**: Deleting a folder is a destructive action that relies on the client having already cleared the folder contents via the file endpoints.

## External consumers

- `concorda-web::src/lib/api.ts::mediaApi.deleteFolder`

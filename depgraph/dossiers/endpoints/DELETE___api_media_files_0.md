---
node_id: DELETE::/api/media/files/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7af7e1740a66c4f1f4ce37bdb9d9e6d9a2c46b94c408b1d10c751ae48cb22d04
status: current
---

# DELETE /api/media/files/{file_id}

## Purpose

Deletes a media file record and its corresponding physical file from the server's storage. This endpoint is used when a user or system removes a file that is no longer needed, ensuring both the database entry and the disk footprint are purged.

## Invariants

- **HTTP status code is 204** upon successful deletion.
- **Requires `current_user` authentication** via the `require_auth` dependency.
- **Requires ownership or management permission** via the `_can_manage_file` check.
- **Deletes both the DB record and the physical file** (unlinks the `disk_path`).
- **Uses `file_id` as the primary identifier** for the lookup.

## Gotchas

- **Order of operations is critical:** The function must check for existence and permissions before unlinking the file to avoid orphaned DB records or unauthorized disk access.
- **Path traversal protection:** Per commit `3e5fdca`, the system relies on the `MediaFile` lookup to resolve the `file_path` rather than accepting a raw path from the client, preventing unauthorized file deletion.
- **Storage structure dependency:** The physical file location is relative to `DOCUMENTS_DIR` (set in commit `283e149`). If the `file_path` in the DB is not a relative path or is malformed, `disk_path.unlink()` may fail or target incorrect directories.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and the internal `_can_manage_file` permission guard.
- **Audit**: (Y) Deletion of media files is a sensitive operation; ensure any calling service logs this intent if tracking file lifecycle is required.
- **Side effects**: Deleting a file may break any active `<img>` or `<video>` tags in the web UI that reference the `file_url`.

## External consumers

- `concorda-web::src/lib/api.ts::mediaApi.deleteFile`

---
node_id: PUT::/api/media/files/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf76e6ca116dbe0308b6b6db4ad33fef4b7e5aa359a40d6592570afb7fcc2591
status: current
---

# PUT /api/media/files/{file_id}

## Purpose

Manages the lifecycle of media files (uploads, metadata updates, and deletions) via the `/api/media/files/{file_id}` endpoint. This node is the primary interface for modifying file attributes like `scope` or `file_url`. It is distinct from the `/serve/` endpoint, which is a read-only streaming path designed for high-concurrency file delivery.

## Invariants

- **Requires `require_auth`** — All operations on this endpoint require a valid authentication token.
- **Uses `_can_manage_file` for mutations** — Both `PUT` and `DELETE` operations require the user to pass the management-level permission check, not just basic access.
- **`PUT` updates are partial** — The `FileUpdate` model uses `exclude_unset=True`, meaning only the fields provided in the request body are mutated.
- **`DELETE` is destructive to disk** — The function performs a physical `unlink()` on the file path in `DOCUMENTS_DIR` before removing the database record.

## Gotchas

- **Manual DB session management for streaming** — Per the docstring and commit `3fee226`, the `/serve/` endpoint (and related file serving logic) must not use the standard `get_db` dependency. Doing so ties the database session to the lifetime of the `FileResponse` stream, which causes `QueuePool TimeoutError` when slow clients download large files.
- **Path Traversal Protection** — The lookup in the serve logic uses an exact `file_url` match (`MediaFile.file_url == expected_url`) rather than a `LIKE` pattern to prevent unauthorized access via manipulated filenames.
- **Scope Validation** — The `scope` field is strictly validated against `VALID_SCOPES`. Attempting to set an unsupported scope results in a 400 error.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and internal permission guards `_can_access_file` and `_can_manage_file`.
- **Rate limit**: Media-related operations are subject to the bulk-email and media magic-byte validation limits (see commit `5f9a046`).
- **Side effects**: Deleting a file via this endpoint removes the physical file from the `DOCUMENTS_DIR` on the server.

## External consumers

- `concorda-web::src/components/boat/boat-photos.tsx` (via `string_url`)
- `concorda-web::src/lib/api.ts` (via `mediaApi.updateFile`)

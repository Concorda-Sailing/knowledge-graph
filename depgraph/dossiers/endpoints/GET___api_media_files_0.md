---
node_id: GET::/api/media/files/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e98f9106de1d49dd5afaa400c87a231daf0085a858f882f2fadb19727bed9d26
status: llm_drafted
---

# GET /api/media/files/{file_id}

## Purpose

Retrieves metadata for a specific media file by its `file_id`. This endpoint is used to fetch the `FileRead` schema (including path and content hash) rather than the file content itself. It is distinct from `/api/media/serve/{filename}`, which is used for the actual binary streaming.

## Invariants

- **Requires Authentication** — Uses `Depends(require_auth)` to ensure a valid `current_user` is present.
- **Returns `FileRead` schema** — Provides metadata like `id`, `file_path`, and `content_hash`.
- **Strict Access Control** — Must pass the `_can_access_file` check; otherwise, returns a 403.
- **404 on Missing ID** — Returns a 404 error if the `file_id` does not exist in the `MediaFile` table.

## Gotchas

- **Session Management for Streaming** — Per commit `3fee226`, the sibling endpoint `/api/media/serve/{filename}` must not use `Depends(get_db)` or `get_current_user` directly in the same way as standard endpoints. Doing so causes the DB session to remain open during the entire `FileResponse` stream, leading to `QueuePool TimeoutError` when multiple clients download large files.
- **IDOR Vulnerability** — Recent security hardening (commit `c9a7c41`) ensures that even with a valid ID, the `_can_access_file` check is mandatory to prevent unauthorized access to files via ID guessing.
- **Pathing Changes** — Per commit `283e149`, file paths are relative to the restructured directory structure `/opt/concorda/{database,photos,documents}`.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` via `current_user`.
- **Rate limit**: Indirectly affected by media service-wide rate limits (see commit `5f9a046`).
- **Side effects**: Changes to file metadata via `PUT` or deletion via `DELETE` affect the visibility of media in the `boatfinder` and `crew invite` systems.

## External consumers

- `concorda-web::src/lib/api.ts::mediaApi.getFile`

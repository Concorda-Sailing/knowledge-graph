---
node_id: GET::/api/admin/storage-info
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a9b206ccdfd62525599f75baa4bb192280afaae1305bc8e663d9d0e1cfadf9b3
status: llm_drafted
---

# GET /api/admin/storage-info

## Purpose

Provides high-level visibility into the server's filesystem usage, specifically targeting the storage footprint of the application's core directories. It calculates the size and file counts for the Photos and Documents directories, alongside the database file, to help administrators monitor disk space consumption. This is a diagnostic tool for infrastructure monitoring rather than a real-time data-fetching endpoint.

## Invariants

- **HTTP Method**: `GET`.
- **Auth**: Requires a valid session via `require_auth`.
- **Authorization**: Must pass the `_require_system_admin` check; standard authenticated users cannot access this endpoint.
- **Response Shape**: Returns a `StorageInfoResponse` containing absolute paths for `data_dir` and `database_path`, and a list of `directories` with human-readable size strings (e.g., "1.2 MB").

## Gotchas

- **Recursive scanning overhead**: The function uses `rglob("*")` to traverse directories. While efficient for small volumes, a massive number of files in `PHOTOS_DIR` or `DOCUMENTS_DIR` could cause a spike in I/O or latency during the scan.
- **Human-readable formatting**: The `_human_size` helper is used for all size displays. If the underlying `stat().st_size` returns unexpected types or if the division logic is altered, the display strings in the UI will break.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_require_system_admin`.
- **Side effects**: None. This is a read-only diagnostic endpoint.

## External consumers

- `concorda-web::src/lib/api.ts::adminStorageApi.get` (used for admin dashboard monitoring).

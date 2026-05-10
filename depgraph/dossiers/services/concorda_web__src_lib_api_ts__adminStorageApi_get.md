---
node_id: concorda-web::src/lib/api.ts::adminStorageApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2f45fb2ec989295304071b215c06f63bda81abed6e5ad7c677cedc61f74f4bf1
status: llm_drafted
---

# adminStorageApi.get

## Purpose

Provides access to the server's storage and filesystem metadata. It retrieves a `StorageInfo` object containing directory paths, database size, and a list of subdirectories. This is used by administrative interfaces to monitor disk usage and system health.

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to access the `/api/admin/storage-info` endpoint.
- **Returns `StorageInfo`** — the response must include `data_dir`, `database_path`, `database_size_display`, and an array of `directories`.
- **Output is for display** — fields like `database_size_display` and `total_size_display` are pre-formatted strings intended for the UI.

## Gotchas

- **Admin-only access** — because it uses `fetchApiAuthenticated`, the caller must have administrative privileges; failure to do so will result in a 401/403 error.
- **UI dependency** — `AdminSystemPage` (the primary consumer) relies on this to render system health metrics.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin credentials).
- **Side effects**: Used by the `AdminSystemPage` to populate system health and storage statistics.

## External consumers

None known.

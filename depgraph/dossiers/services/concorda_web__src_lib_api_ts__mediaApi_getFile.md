---
node_id: concorda-web::src/lib/api.ts::mediaApi.getFile
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4384ba09e8e6556c299bc59e67765c4816db069c27823df46dd3d0701404ad38
status: llm_drafted
---

# mediaApi.getFile

## Purpose

Fetches a single media file by its unique identifier. This is the granular counterpart to `mediaApi.listFiles`, which returns collections of files based on folder or entity context. Use this when you have a specific `id` and need the full `MediaFile` object (including metadata like `picture_url`).

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to execute.
- **Returns a single `MediaFile` object** — the response shape is not an array.
- **Endpoint path is `/api/media/files/${id}`** — follows the standard RESTful pattern for resource retrieval.

## Gotchas

- **`upload` uses a different authentication pattern** — unlike the other methods in this service that use `fetchApiAuthenticated`, `upload` manually calls `getAuthToken()` and uses a standard `fetch` to handle `FormData`. If you are refactoring the auth layer, ensure you don't break the manual header injection in `upload`.

## Cross-cutting concerns

- **Auth**: Depends on `fetchApiAuthenticated` (and `getAuthToken` for the `upload` method).
- **Side effects**: Updates to files via `updateFile` or `deleteFile` will affect the visibility of assets in the UI components that consume this data.

## External consumers

None known.

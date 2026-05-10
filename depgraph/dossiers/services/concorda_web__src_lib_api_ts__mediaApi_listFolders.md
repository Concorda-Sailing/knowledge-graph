---
node_id: concorda-web::src/lib/api.ts::mediaApi.listFolders
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 70ba404ba969bcbfd6faf891ad58212ab9ecb85a0224c816fcceb269d76ce69b
status: llm_drafted
---

# mediaApi.listFolders

## Purpose

Provides an interface for managing and retrieving the hierarchical structure of media folders. It allows for listing, creating, updating, and deleting folders, typically used to organize media files (like boat photos) by a parent directory or owner. Use this instead of `directoryApi` when the operation specifically concerns the media-file-to-folder relationship.

## Invariants

- **Uses `fetchApiAuthenticated`** — all calls require a valid bearer token and are subject to the standard authentication flow.
- **`listFolders` uses URLSearchParams** — parameters like `parent_uuid` and `owner_uuid` are appended as query strings to the base `/api/media/folders` path.
- **Returns `MediaFolder[]` on list** — the successful response for a list operation is an array of folder objects.
- **`createFolder` requires a name** — the `data` object must include a `name` string to be valid.

## Gotchas

- **Error detail extraction** — if a request fails, the error object attempts to parse the response body for a `detail` field (per the logic in the `res.ok` check) to provide a human-readable error message rather than a generic status code.
- **Dependency on `fetchApiAuthenticated`** — if the authentication wrapper is modified, the error handling for media folder operations (specifically the `try/catch` block in the response handler) may behave differently.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Changes to folder structure (via `createFolder`, `updateFolder`, or `deleteFolder`) will affect the visibility and organization of media assets in components like `BoatPhotos`.

## External consumers

- `concorda-web::src/components/boat/boat-photos.tsx` (via `BoatPhotos` component).

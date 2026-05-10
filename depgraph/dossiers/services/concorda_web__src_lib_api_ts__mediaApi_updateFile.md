---
node_id: concorda-web::src/lib/api.ts::mediaApi.updateFile
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9ad338fb23ab14560f1c65f3ee079d5ad9e0f460a655e8880a8911ed4d3ebee6
status: current
---

# mediaApi.updateFile

## Purpose

The `updateFile` method performs a partial update (PATCH-like behavior via `PUT`) on a specific media file's metadata. It is used to rename files, move them between folders, or update their association with specific entities (like a boat or a document type). Use this when you need to modify the properties of an existing file rather than re-uploading the binary.

## Invariants

- **HTTP Method is `PUT`** — unlike `upload` which uses `POST`, this method targets an existing resource ID.
- **Returns `MediaFile`** — the response body is the updated file object, allowing the UI to immediately reflect name or path changes.
- **Requires a valid `id`** — the first argument must be the unique identifier of the file being modified.
- **Uses `fetchApiAuthenticated`** — the request must include the bearer token via the standard authentication wrapper.

## Gotchas

- **Partial updates via `JSON.stringify`** — the `data` object accepts optional fields (`name`, `folder_uuid`, etc.). If a field is omitted from the object, it is not sent in the body, but the API behavior for omitted fields (whether they clear the value or leave it unchanged) depends on the backend implementation of the `PUT` handler.
- **`upload` vs `updateFile` distinction** — `upload` (line 2893) handles `FormData` and binary files, whereas `updateFile` (line 2886) only handles JSON metadata. Attempting to pass a `File` object to `updateFile` will fail at the TypeScript level or result in an empty body.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the file.
- **Side effects**: Updates to file names or folder locations may affect the visibility of assets in the `AdminFilesPage` and `BoatDocuments` component.

## External consumers

- `AdminFilesPage` (via `mediaApi.updateFile`)
- `BoatDocuments` (via `mediaApi.updateFile`)

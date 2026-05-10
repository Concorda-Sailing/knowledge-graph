---
node_id: concorda-web::src/lib/api.ts::mediaApi.updateFolder
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 75b4ee09e42df90d9683d9095d3e55941b140a744367f978f313d4d093891f73
status: llm_drafted
---

# mediaApi.updateFolder

## Purpose

The `updateFolder` method performs a partial update on a specific media folder via a `PUT` request. It is used to modify metadata such as the folder name, its associated entity type/UUID, or its scope. Use this method when you need to rename a folder or re-parent it within the media hierarchy, rather than `createFolder` which is used for initial instantiation.

## Invariants

- **Method is `PUT`** — All updates are sent via the `PUT` verb to the specific resource URI.
- **Requires a valid `id`** — The first argument must be the string identifier of the folder being modified.
- **Returns `MediaFolder`** — The response body contains the updated folder object, allowing the UI to immediately reflect changes (e.g., new name or scope).
- **Uses `fetchApiAuthenticated`** — The request must include the bearer token and follows the standard authenticated session lifecycle.

## Gotchas

- **Partial updates are supported** — The `data` object allows optional fields (`name?`, `entity_type?`, etc.). If a field is omitted from the payload, the existing value on the server remains unchanged.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the media structure.
- **Side effects**: Changes to folder names or scopes may affect how media assets are categorized or displayed in the file browser UI.

## External consumers

None known.

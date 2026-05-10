---
node_id: concorda-web::src/lib/api.ts::mediaApi.deleteFolder
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0dfb6f6d3b8664231efb7c15f22279b7a7161630cdc2965e3fa2072a53ce31f7
status: current
---

# mediaApi.deleteFolder

## Purpose

The `deleteFolder` method performs a destructive operation on a media folder via a `DELETE` request. It is used to remove organizational media structures, and an agent should use this instead of `updateFolder` when the intent is to remove the folder entirely rather than just renaming or re-scoping it.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb.
- **Requires `fetchApiAuthenticated`** — The call is wrapped in the authenticated fetch helper, requiring a valid bearer token.
- **Returns `void`** — The method returns a promise that resolves to nothing upon successful deletion.
- **Target is a specific resource ID** — The endpoint is constructed as `/api/media/folders/${id}`.

## Gotchas

- **Directly impacts `BoatPhotos` component** — As seen in `boat-photos.tsx:243`, this method is used by the photo management UI. Deleting a folder here will immediately remove the associated media structure from the view.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the media structure.
- **Side effects**: Deleting a folder will affect the visibility and availability of media assets within the `BoatPhotos` component.

## External consumers

- `concorda-web::src/components/boat/boat-photos.tsx` (via `BoatPhotos` component)

---
node_id: concorda-web::src/lib/api.ts::mediaApi.createFolder
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0cd3ffa8032f53e1b246f803cbf5920cf5d58889542b3f06ad7e2ba25cd96c31
status: llm_drafted
---

# mediaApi.createFolder

## Purpose

The `createFolder` method is a service for creating new media directories within the media storage hierarchy. It is used to organize assets (like boat photos or event media) into logical groupings. It is distinct from `listFolders` or `updateFolder` in that it is the only method in the `mediaApi` that accepts a full payload to instantiate a new resource.

## Invariants

- **Method is `POST`** — Always uses the `POST` verb to the `/api/media/folders` endpoint.
- **Requires `fetchApiAuthenticated`** — The request must include the bearer token via the authenticated fetch wrapper.
- **Return type is `MediaFolder`** — A successful call returns the newly created folder object.
- **Payload structure** — The `data` object must include at least a `name` and a `parent_uuid` (if nesting) to be valid for the API.

## Gotchas

- **Dependency on `fetchApiAuthenticated`** — Like other media methods, this relies on the authenticated session; if the token is missing or expired, the folder creation will fail at the network level.
- **Structural dependency** — The `BoatPhotos` component in `src/components/boat/boat-photos.tsx` (at line 209) depends on the media API structure; changes to the expected shape of a folder or its parentage may break the photo upload/display flow.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Creating a folder may impact the visibility of media assets in the `BoatPhotos` component if the folder is used for organization.

## External consumers

None known.

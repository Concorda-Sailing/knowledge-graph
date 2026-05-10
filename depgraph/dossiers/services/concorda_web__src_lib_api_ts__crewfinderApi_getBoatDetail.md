---
node_id: concorda-web::src/lib/api.ts::crewfinderApi.getBoatDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea9a4481a39a9ed6616b9e7f50c65e7a68ed940c44ec35106306e604b500939c
status: llm_drafted
---

# crewfinderApi.getBoatDetail

## Purpose

Fetches the detailed profile of a boat within the Crewfinder context. It is a specialized sibling to `getCrewDetail`, used specifically when the UI needs to display boat-specific metadata (like configuration or status) rather than person-specific data. Use this when navigating to a boat's detail page to ensure the correct `BoatCrewfinderProfileDetail` shape is returned.

## Invariants

- **Method is GET** via `fetchApiAuthenticated`.
- **Path is strictly formatted** as `/api/crewfinder/detail/boat/{boatId}`.
- **`boatId` must be URI encoded** via `encodeURIComponent` to prevent path traversal or malformed requests.
- **Returns `BoatCrewfinderProfileDetail`** which contains boat-specific attributes distinct from a person's profile.

## Gotchas

- **Shape mismatch risk**: Per commit `bf15808`, there is a history of issues where the API returns a shape that doesn't match the expected frontend model (specifically regarding `boat_config_id`). Ensure the returned object matches the `BoatCrewfinderProfileDetail` interface to avoid runtime errors in the `BoatDetailPage`.
- **Dependency on `fetchApiAuthenticated`**: Like all methods in this service, it relies on a valid bearer token being present in the auth state; if the user is not authenticated, this will fail before reaching the endpoint.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid session/token).
- **Side effects**: Data fetched here populates the `BoatDetailPage` (see `concorda-web::src/app/members/crewfinder/boat/[id]/page.tsx`).

## External consumers

- `concorda-web::src/app/members/crewfinder/boat/[id]/page.tsx` (BoatDetailPage)

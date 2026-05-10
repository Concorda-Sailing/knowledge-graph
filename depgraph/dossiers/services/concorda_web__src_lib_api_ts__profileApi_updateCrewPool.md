---
node_id: concorda-web::src/lib/api.ts::profileApi.updateCrewPool
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b1318d45248a0d23306c9d787fba3f25e09c5158cbf181c5a2a95e45da3d5369
status: llm_drafted
---

# profileApi.updateCrewPool

## Purpose
`updateCrewPool` is a specialized API wrapper used to modify the properties of an existing crew pool within a specific boat's scope. It is distinct from `createCrewPool` (which uses POST) and `listCrewPools` (which is a GET request). A future agent should reach for this function when a user is editing the name or the membership list of an existing pool, rather than creating a new one.

## Invariants
*   **HTTP Method/Path**: Uses `PUT` on `/api/profile/boats/${boatId}/crew-pools/${poolId}`.
*   **Auth Requirement**: Requires an authenticated session via `fetchApiAuthenticated`.
*   **Return Shape**: Returns the updated `CrewPool` object upon success.
*   **Required Fields**: The `data` object accepts optional `name` (string) and `member_ids` (array of strings).
*   **Scope**: Operations are strictly scoped to the provided `boatId`.

## Gotchas
*   **Partial Updates**: The `data` object uses optional properties (`name?`, `member_ids?`). Ensure the client-side state management accounts for the fact that omitting a field in the payload might be interpreted by the backend as a request to keep the existing value or (depending on backend implementation) clear it.
*   **ID Dependency**: Both `boatId` and `poolId` are required in the URL path; failure to provide a valid `poolId` will result in a 404 or routing error.

## Cross-cutting concerns
*   **Auth**: Relies on `fetchApi-authenticated` to ensure the user has permission to modify the boat's resources.
*   **Side Effects**: Changes to crew pools may impact the visibility of crew availability in the dashboard or event-specific views.

## External consumers
*   `concorda-web::src/components/dashboard/my-crew-tab.tsx` (via `MyCrewTab` component).

## Open questions
*   Does the backend support partial updates (PATCH-style) for the `member_ids` array, or must the full list be sent to avoid accidental deletions?

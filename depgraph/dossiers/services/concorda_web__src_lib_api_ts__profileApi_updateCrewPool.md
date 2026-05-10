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

Updates the configuration of an existing crew pool for a specific boat. It is used to modify the `name` or the list of `member_ids` associated with a pool. This is a specialized update method for boat-scoped resources, distinct from the broader `eventsApi` or `seriesApi` methods.

## Invariants

- **HTTP Method is `PUT`** — performs a full replacement of the specific resource fields.
- **Path structure is `/api/profile/boats/${boatId}/crew-pools/${poolId}`** — requires both `boatId` and `poolId` to target the correct resource.
- **Payload is a partial update** — the `data` object accepts optional `name` and `member_ids`.
- **Returns the updated `CrewPool` object** — allows the caller to immediately sync local state with the server response.

## Gotchas

- **Requires `fetchApiAuthenticated`** — as a profile-scoped action, it relies on the bearer token established via the auth flow.
- **Boat-scoped dependency** — the `boatId` must be valid for the authenticated user's profile context; attempting to update a pool for a boat the user does not own/access will result in a 403 or 404.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the boat's crew configuration.
- **Side effects**: Updates to crew pools via this method impact the visibility of crew status on the `MyCrewTab` component in the dashboard.

## External consumers

None known.

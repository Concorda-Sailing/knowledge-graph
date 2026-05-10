---
node_id: PUT::/api/profile/boats/{0}/crew-pools/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1ae5d11eb2b1d6a24c1b6ef9b6c884fde01a3fd95f3e6e565e5a5e3a310dca55
status: current
---

# PUT /api/profile/boats/{boat_id}/crew-pools/{pool_id}

## Purpose

Updates the metadata (name) or the membership (member_ids) of a specific crew pool within a boat. This endpoint is used by boat owners to manage their crew rosters. It is distinct from the `DELETE` method on the same path, which removes the pool entirely.

## Invariants

- **Method**: `PUT`.
- **Auth**: Requires a valid session via `require_auth`.
- **Authorization**: Must pass the `_require_boat_owner` check; only the boat owner can modify the pool.
- **Input Shape**: Expects a `CrewPoolUpdate` object.
- **Return Shape**: Returns the updated `CrewPoolRead` object.
- **Scope**: The `pool_id` must belong to the `boat_id` provided in the URL.

## Gotchas

- **Ownership Requirement**: The `_require_boat_owner` guard is strictly enforced. If the `current_user` is not the owner of the `boat_id`, the request will fail.
- **Scope Change**: Per commit `770d190`, crew pools are now scoped to the `boat` rather than the `person`. Ensure any logic attempting to move pools between boats is aware of this structural change.
- **Cascade/Snapshot Risks**: Per commit `d54327b`, modifications to boat configurations can have cascading effects on `positions_needed` snapshots and `EventCrew` assignments. Use caution when altering pool structures that might impact event-side data.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_boat_owner`.
- **Side effects**: Changes to crew pools may affect the visibility of crew members in the boat-finder or event-specific roster views.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.updateCrewPool`

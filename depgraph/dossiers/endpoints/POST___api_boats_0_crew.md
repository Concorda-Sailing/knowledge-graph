---
node_id: POST::/api/boats/{0}/crew
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2dd79e3724fd35f072ae430c2132d198967bddb26dce97ca4df31e542f2b8721
status: llm_drafted
---

# POST /api/boats/{boat_id}/crew

## Purpose

Adds a new person to a boat's crew. This endpoint is the primary way to establish a formal link between a `Person` and a `Boat`, assigning them a specific role and position. It is distinct from the `reorder` endpoint, as this creates the record, while `reorder` only modifies the `priority` field of existing members.

## Invariants

- **HTTP Method/Path**: `POST /api/boats/{boat_id}/crew`.
- **Authentication**: Requires a valid session via `require_auth`.
- **Authorization**: Only the boat owner (verified via `_require_owner`) can call this endpoint.
- **Return Shape**: Returns a `BoatCrewRead` object containing the person's details and the assigned role/position.
- **Uniqueness**: A person cannot be added to the same boat twice; the system raises a `409 Conflict` if the `person_uuid` is already present in the boat's crew.

## Gotchas

- **Ownership Check**: The `_require_owner` guard is critical; without it, any authenticated user could inject crew members into any boat.
- **Race Conditions**: While the `409 Conflict` check is present, high-frequency concurrent calls for the same `person_uuid` could theoretically bypass the check before the first `db.commit()` completes.
- **Role/Position Defaults**: The `role` and `position` are passed via the `BoatCrewCreate` model; ensure the frontend provides valid enum values to avoid validation errors.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_owner` to ensure only the boat owner can modify the crew.
- **Websocket**: Emits the `BOAT_CREW_UPDATED` event via `broadcast_event` upon successful creation.
- **Audit**: N/A.
- **Side effects**: Triggers updates to any UI components listening for `BOAT_CREW_UPDATED` (e.g., the boat's crew list view).

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.addCrew`

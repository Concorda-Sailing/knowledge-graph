---
node_id: PUT::/api/boats/{0}/crew/reorder
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 094f06f988522a3305473b7b60011494c7201644fc22efc7995b965ad5f3423e
status: current
---

# PUT /api/boats/{boat_id}/crew/reorder

## Purpose

Reorders the priority of crew members for a specific boat. It accepts an ordered list of `person_uuids` where the index in the list determines the new `priority` value. This is used to allow boat owners to visually re-rank their crew members in the UI.

## Invariants

- **Method/Path**: `PUT /{boat_id}/crew/reorder`.
- **Auth**: Requires `require_auth` and passes through `_require_owner` to ensure only the boat owner can change the order.
- **Input Shape**: Expects `CrewReorderRequest` containing a `list[str]` of `person_uuids`.
- **Ordering Logic**: The position (index) in the input list directly maps to the `priority` integer in the database.
- **Return Shape**: Returns a `list[BoatCrewRead]` representing the updated, ordered crew members.

## Gotchas

- **Ownership is mandatory**: The `_require_owner` check is critical; if an agent attempts to reorder crew for a boat they do not own, the request will fail.
- **Implicit Priority Mapping**: The function assumes the input list is the definitive source of truth for order. If a `person_uuid` is passed that is not currently in the `crew_map`, that specific person's priority is not updated, but the loop continues.

## Cross-cutting concerns

- **Auth**: Uses `_require_owner` to validate that the `current_user.id` matches the boat's owner.
- **Websocket**: Emits `BOAT_CREW_UPDATED` via `broadcast_event` upon successful commit.
- **Side effects**: Triggers updates to any UI components listening for `BOAT_CREW_UPDATED` (e.g., the boat's crew list view).

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.reorderCrew`

---
node_id: PUT::/api/boats/{0}/punchlist/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85c0248826a5e1be1f2ce42bf73b2d9abe8ff72598fb36797cc9c46f4aa9dcf1
status: llm_drafted
---

# PUT /api/boats/{boat_id}/punchlist/{item_id}

## Purpose

Updates an existing punchlist item for a specific boat. This endpoint allows for partial updates to item properties (via `exclude_unset=True`) and is used to maintain the boat's maintenance or task list. It is distinct from the creation endpoint, as it requires an existing `item_id` and enforces strict membership-based authorization.

## Invariants

- **Method is `PUT`** — performs a partial update of the `BoatPunchlistItem`.
- **Auth required** — uses `require_auth` to ensure the user is logged in.
- **Authorization check** — calls `_require_crew_or_owner` to ensure the user has permission to modify the boat's data.
- **Return shape** — returns a `PunchlistItemRead` object representing the updated state.
- **Broadcasts on change** — triggers a `PUNCHLIST_UPDATED` event upon successful commit.

## Gotchas

- **Authorization hierarchy** — per `_require_crew_or_owner`, any active crew member can update an item, but only the creator or the boat owner can delete it (see `delete_punchlist_item` logic).
- **IDOR protection** — the function explicitly filters by both `item_id` and `boat_id` to ensure an item cannot be updated by referencing a valid ID from a different boat.
- **Recent security hardening** — per commit `c9a7c41`, this endpoint and its related logic were part of a tier-A IDOR audit to ensure users cannot manipulate boat resources they do not belong to.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes the `current_user.id` to `_require_crew_or_owner`.
- **Websocket**: Emits `PUNCHLIST_UPDATED` for the specific `boat_id` on successful update.
- **Side effects**: Updates to this endpoint will trigger UI refreshes for any component listening to the boat's punchlist state.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.updatePunchlistItem`

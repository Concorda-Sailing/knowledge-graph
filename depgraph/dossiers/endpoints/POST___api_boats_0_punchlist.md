---
node_id: POST::/api/boats/{0}/punchlist
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 620e647e986a36b474a55324679fa2b6c358f820ccfca18c19d7ae8149b0ee16
status: llm_drafted
---

# POST /api/boats/{boat_id}/punchlist

## Purpose

Provides the interface for managing a boat's punchlist (maintenance/task items). It allows for creating, updating, and deleting items that represent pending tasks for a specific boat. Use this endpoint when a user needs to report or track maintenance-related issues that require attention from the crew or owner.

## Invariants

- **POST** returns a `201 Created` status with the full `PunchlistItemRead` object.
- **Auth requirement**: Requires a valid `current_user` via `require_auth`.
- **Authorization logic**: Creation and updates require the user to be a member of the boat's crew or the owner (via `_require_crew_or_owner`).
- **Deletion restriction**: Only the creator of the item or the boat owner can perform a deletion.
- **Data shape**: The `title` and `description` are the primary text fields; `importance` is a required field in the creation payload.

## Gotchas

- **Authorization mismatch**: Per commit `36ef425`, the endpoint relies on a tightened boat-crew authz/approval-staged status. Ensure the user's membership status is correctly reflected in the `_require_crew_or_owner` check to avoid unexpected 403s.
- **Deletion permissions**: Unlike creation/update, the `delete_punchlist_item` function does not call `_require_crew_or_owner`, but relies on the `_get_boat_or_404` check and the internal logic that restricts deletion to the creator or owner.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_crew_or_owner` to enforce crew-level permissions.
- **Websocket**: Emits `PUNCHLIST_UPDATED` event with the `boat_id` upon successful creation, update, or deletion.
- **Side effects**: Triggers real-time updates for any UI components listening to the `PUNCHLIST_UPDATED` event for the specific boat.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.createPunchlistItem`

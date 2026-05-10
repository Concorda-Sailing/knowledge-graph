---
node_id: PUT::/api/boats/{0}/crew/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6360f771ea9997d90b7f5e380d389071df9689017065afd56eaed1a26850bc81
status: llm_drafted
---

# PUT /api/boats/{boat_id}/crew/{crew_id}

## Purpose

Updates the role, position, or status of an existing crew member for a specific boat. This endpoint is the primary way to modify a person's metadata within a boat's roster. It is distinct from the `DELETE` method in that it handles both metadata updates and the transition of roles, though it enforces strict ownership-based workflows for sensitive role changes.

## Invariants

- **Method is `PUT`** and requires a `boat_id` and `crew_id`.
- **Requires `AuthUser` via `require_auth`**; the user must be the boat owner to modify crew.
- **Enforces `_require_owner`**; only the boat owner can successfully call this endpoint.
- **Returns `BoatCrewRead`**; the response includes the updated crew object and the associated person's data.
- **Role transitions are restricted.** Direct modification of the `role` field to "owner" (or from "owner") is prohibited to prevent bypassing the co-owner approval workflow.

## Gotchas

- **Role transition restriction:** Per the logic in `update_crew`, attempting to change a role to or from "owner" via this endpoint will raise a `400 Bad Request`. This is a deliberate guard to ensure that owner/co-owner transitions follow the formal approval flow (see `POST /coowner-invite`, etc.) rather than being a simple field update.
- **Ownership requirement:** The endpoint relies on `_require_owner(db, boat_id, current_user.id)`. If the user is not the owner, they cannot modify any crew member, even if they are a co-owner or a high-ranking crew member.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and `_require_owner` (boat owner).
- **Websocket**: Emits `BOAT_CREW_UPDATED` via `broadcast_event` upon successful commit.
- **Side effects**: Triggers updates to any UI components listening to the `BOAT_CREW_UPDATED` event, such as the boat's crew list or member status badges.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.updateCrew` (via `string_url`).

---
node_id: GET::/api/boats/{0}/punchlist
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b81f418da65218f5a6cdefbd635f2e31555df71e0213b77c54d75230071fc080
status: llm_drafted
---

# GET /api/boats/{boat_id}/punchlist

## Purpose

Provides a list of maintenance or repair items (the "punchlist") associated with a specific boat. This endpoint is used by crew members to track and manage tasks that require attention to the vessel. It is distinct from the general event or schedule endpoints, focusing specifically on the physical state and maintenance requirements of the boat.

## Invariants

- **Method**: `GET`
- **Path**: `/{boat_id}/punchlist`
- **Auth**: Requires a valid session via `require_auth`.
- **Access Control**: Only active crew members or the boat owner can access this list, enforced by `_require_crew_or_owner`.
- **Return Shape**: Returns a list of `PunchlistItemRead` objects, ordered by `created` date in descending order.

## Gotchas

- **Authorization tightening**: Per commit `36ef425`, the security model for boat access was tightened; ensure that any logic assuming broad access to boat-related data respects the `_require_crew_or_owner` guard to prevent unauthorized visibility.
- **Ownership vs. Crew**: Recent refactors (e.g., `ea4fcb2`) have hardened how visibility and membership are handled; ensure that `current_user.id` is correctly passed to the dependency to satisfy the `_require_crew_or_owner` check.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and the internal `_require_crew_or_owner` guard.
- **Websocket**: The `POST` and `PUT` siblings of this endpoint emit the `PUNCHLIST_UPDATED` event for the given `boat_id` to trigger real-time UI updates.
- **Side effects**: Changes to the punchlist (via POST/PUT) trigger a broadcast that may affect the real-time state of the boat's dashboard or detail views in the web client.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.getPunchlist`

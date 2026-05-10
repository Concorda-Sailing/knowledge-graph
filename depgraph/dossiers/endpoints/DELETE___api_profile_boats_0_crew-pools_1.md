---
node_id: DELETE::/api/profile/boats/{0}/crew-pools/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fb535ded087068dc61526bb993c488d328686d29fd99db067c8b809a9ffb0155
status: llm_drafted
---

# DELETE /api/profile/boats/{boat_id}/crew-pools/{pool_id}

## Purpose

Deletes a specific crew pool associated with a boat. This is a destructive operation used to remove organizational crew structures. It is distinct from event-level crew management; this endpoint manages the high-level availability of crew pools at the boat/profile level.

## Invariants

- **HTTP Method:** `DELETE`
- **Path:** `/api/profile/boats/{boat_id}/crew-pools/{pool_id}`
- **Auth:** Requires a valid session via `require_auth`.
- **Ownership:** The `current_user` must be the owner of the `boat_id` to execute the deletion (enforced by `_require_boat_owner`).
- **Return Shape:** Returns a `204 No Content` on success.
- **Error State:** Returns `404 Not Found` if the `pool_id` does not exist or is not associated with the provided `boat_id`.

## Gotchas

- **Ownership Enforcement:** Per `_require_boat_owner`, this is not a global delete; it is strictly scoped to the boat owner.
- **Scope Change:** Per commit `770d190`, crew pools are now scoped to the `boat` rather than the `person`. Any logic assuming a person-centric pool structure will fail.
- **Cascade Risks:** Recent history (commit `d54327b` and `31aa70d`) shows frequent churn regarding how changes to boat configurations cascade to `positions_needed` and `EventCrew` assignments. Deleting a pool may have downstream effects on event-level data that are not explicitly handled by a database cascade but are managed by the application logic.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_boat_owner` to gate access.
- **Side effects**: Deleting a pool may affect the visibility of crew availability in the boat's profile and related event-level roster views.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.deleteCrewPool`

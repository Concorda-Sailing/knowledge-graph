---
node_id: GET::/api/profile/boats/{0}/crew-pools
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 074be389324419235e10728940f7cff57238acb81cc158e46689661d8b36946f
status: current
---

# GET /api/profile/boats/{boat_id}/crew-pools

## Purpose

Retrieves a list of all `CrewPool` objects associated with a specific `boat_id`. This endpoint is used by the web UI to display organized groups of members (e.g., "Racing Team" or "Social Crew") that can be assigned to events. It is distinct from the general profile or boat configuration endpoints as it focuses specifically on the sub-resource of crew-grouping.

## Invariants

- **Method is `GET`** and requires a valid `boat_id` in the path.
- **Returns a list of `CrewPoolRead` objects.** Each object includes the pool name and the list of `member_ids`.
- **Ordering is strict.** Results are returned ordered by `CrewPool.name` ascending.
- **Ownership is mandatory.** The request must be made by the boat owner; otherwise, the request fails.

## Gotchas

- **Scope change from person to boat.** Per commit `770d190`, crew pools were refactored to be scoped to a `boat` rather than a `person`. Any logic attempting to access pools via a user-centric model will fail.
- **Cascade behavior.** Per commit `31aa70d`, changes to boat configuration (including potentially these pools) are intended to cascade to `positions_needed` snapshots and clear orphan `EventCrew` assignments.
- **Authorization guard.** This endpoint relies on the `_require_boat_owner` helper. If the `current_user` is not the owner of the `boat_id` provided, the request will be rejected.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes the `_require_boat_owner` check.
- **Side effects**: Changes to these pools (via the sibling POST/PUT/DELETE endpoints) impact the `positions_needed` snapshot and `EventCrew` assignments.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.listCrewPools`

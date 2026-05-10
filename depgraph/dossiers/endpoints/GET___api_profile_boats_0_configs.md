---
node_id: GET::/api/profile/boats/{0}/configs
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9804ef2ca3b28ee99db99e9c48322aadcd6cf5c98e06c4b7f79fd057606493d8
status: current
---

# GET /api/profile/boats/{boat_id}/configs

## Purpose

Retrieves the list of crew configurations associated with a specific boat. This endpoint is used to populate the configuration management UI, allowing users to manage different sets of crew roles and positions. It is distinct from person-level crew pools, as it is scoped strictly to the `boat_id` and requires ownership of that boat to access.

## Invariants

- **Method is `GET`** and returns a list of `BoatConfigRead` objects.
- **Requires `boat_id`** as a path parameter.
- **Authentication is mandatory** via the `require_auth` dependency.
- **Ownership is strictly enforced** via the `_require_boat_owner` guard.
- **Ordering is deterministic**, sorted by `sort_order` and then by `name`.

## Gotchas

- **Single Default Constraint:** Only one configuration per boat can have `is_default = true`. The `POST` and `PUT` methods in this module handle the logic of setting the previous default to `False` when a new default is assigned (see `create_boat_config` and `update_boat_config`).
- **Recent IDOR protection:** Per commit `c9a7c41`, ensure any new logic involving this endpoint respects the `_require_boat_owner` check to prevent unauthorized access to boat configurations.
- **Cascading logic:** Per commit `d54327b`, modifications to configurations may have side effects on `positions_needed` snapshots and `EventCrew` assignments; be cautious when altering the schema of the configuration objects.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_boat_owner(boat_id, current_user, db)` to ensure the requester has permission to view/manage the boat's settings.
- **Side effects**: Changes to these configurations (via the sibling POST/PUT methods) impact the `positions_needed` snapshot and can affect how `EventCrew` assignments are cleared or updated.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.listBoatConfigs`

## Open questions

- Should the API support a "soft-delete" or "archived" state for configurations, or should they be permanently removed from the list?

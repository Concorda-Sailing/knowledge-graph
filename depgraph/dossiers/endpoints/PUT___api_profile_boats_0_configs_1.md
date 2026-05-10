---
node_id: PUT::/api/profile/boats/{0}/configs/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 28e3d6bb527fbb177385d0e000a5493b9c7cd7f90dd1ace2477b1e00d831d52c
status: llm_drafted
---

# PUT /api/profile/boats/{boat_id}/configs/{config_id}

## Purpose

Updates an existing `BoatConfig` for a specific boat. This method is used to modify configuration properties (like names or settings) and handles the critical logic of ensuring that only one configuration is marked as the "default" for a given boat at any time.

## Invariants

- **HTTP Method**: `PUT`.
- **Path**: `/api/profile/boats/{boat_id}/configs/{config_id}`.
- **Auth**: Requires `require_auth` and passes through the `_require_boat_owner` guard.
- **Return Shape**: Returns the updated `BoatConfigRead` object.
- **Default Constraint**: If `is_default` is set to `True` in the request, all other configurations for that `boat_id` must have `is_default` set to `False`.

## Gotchas

- **Single Default Enforcement**: Per commit `09f19fa`, this endpoint enforces that only one configuration per boat can be the default. If a user sets a new config as default, the previous default is automatically unset.
- **Cascading Edits**: Per commit `31aa70d` (and reverted in `d54327b`), changes to boat configurations can have side effects on `positions_needed` snapshots and `EventCrew` assignments. Be cautious when modifying the schema or logic of how configurations are applied to ensure these downstream effects remain consistent.

## Cross-cutting concerns

- **Auth**: Uses `_require_boat_owner` to ensure the `current_user` has ownership rights over the `boat_id` before allowing updates.
- **Side effects**: Changes to configurations may affect the accuracy of `positions_needed` snapshots in the event/sailing-event domain.

## External consumers

- `concorda-web` (via `profileApi.updateBoatConfig`).

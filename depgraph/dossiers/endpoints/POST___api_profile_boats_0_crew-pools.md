---
node_id: POST::/api/profile/boats/{0}/crew-pools
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 57359678ff4018768a20cfa29ad44044a4a9206159876c9ab67489ae5e20ccfa
status: current
---

# POST /api/profile/boats/{boat_id}/crew-pools

## Purpose

Creates a new `CrewPool` associated with a specific boat. This endpoint allows boat owners to group members together for organizational purposes. It is distinct from individual user-level crew management; it is a boat-centric grouping mechanism.

## Invariants

- **HTTP Method**: `POST`
- **Path**: `/api/profile/boats/{boat_id}/crew-pools`
- **Auth**: Requires a valid session via `require_auth`.
- **Ownership**: The request is strictly gated by `_require_boat_owner(boat_id, ...)`.
- **Return Shape**: Returns a `CrewPoolRead` object containing the new `id`, `boat_uuid`, `name`, and `member_ids`.

## Gotchas

- **Scope Change**: Per commit `770d190`, crew pools are now scoped to a `boat` rather than a person. Ensure any logic attempting to associate pools with users directly is updated to follow this boat-centric pattern.
- **Cascading Edits**: Per commit `d54327b`, be aware that edits to boat configurations can trigger cascades to `positions_needed` snapshots and clear orphan `EventCrew` assignments. This endpoint's side effects on the boat state may impact these downstream snapshots.
- **Single Default Constraint**: Per commit `09f19fa`, the system enforces a single default per boat; ensure that creating or updating pools does not violate the implicit single-default-per-boat logic used in higher-level boat configurations.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and the `_require_boat_owner` guard.
- **Side effects**: Changes to crew pools may affect the `positions_needed` snapshot and `EventCrew` assignments for the boat.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.createCrewPool`

---
node_id: concorda-web::src/lib/api.ts::profileApi.createBoatConfig
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fc83ac063b441d7a19743683c8808e93ec1c15542032288904617171a504a150
status: current
---

# profileApi.createBoatConfig

## Purpose
Client-side mirror for creating a new BoatConfig (a named "position set" / crew configuration) on an already-owned boat. A BoatConfig is the spatial layout of crew positions — name, config_type, and a `positions[]` of `{name, location_x, location_y, count?}` — that drives the boat-positions diagram and is the denominator for "X accepted of Y" on schedule cards. POSTs `/api/profile/boats/{boatId}/configs`. This is the "I'm setting up Spinnaker vs No-Spin trim layouts for my J/24" entry point — not boat creation. The caller must already be the active owner of `boatId`; the backend enforces it via `_require_boat_owner`.

## Invariants
- `boatId` must reference a Boat where the current user has an active `BoatCrew` row with `role="owner"` — otherwise the backend 403s.
- `BoatConfigCreate` requires `name`, `config_type`, `positions[]`; `is_default` defaults to `false`.
- New config's `sort_order` is server-assigned to the current count of sibling configs (append at end).
- If `is_default=true` is sent, the backend demotes any existing default for the same boat in the same transaction — exactly one default per boat.
- Returns the persisted `BoatConfig` (id, boat_uuid, sort_order, timestamps populated).

## Gotchas
- Easy to confuse with `profileApi.createBoat` (line 1312) — that's the J/24-registration entry point and seeds the owner BoatCrew. This call assumes the boat already exists.
- `BoatConfigPosition` on the client uses `location_x`/`location_y`, but the backend column type is `list[dict]` (untyped JSON) — drift is possible. `bf15808` ("use stored boat_config_id instead of shape-matching") shows the system has been bitten by shape-based matching of configs; prefer ID references.
- `count?` on a position is optional and feeds slot-count math; missing `count` is treated as 1 by some consumers (see `b4d60c6`).
- Setting `is_default` silently mutates a sibling row — UI should refresh the full `listBoatConfigs` after create, not just append.
- Backend uses `data.is_default` directly into the model without the `or False` coercion; relies on the Pydantic default.

## Cross-cutting concerns
- Auth: `require_auth` + `_require_boat_owner` — owners only, not co-owners-in-other-roles, not crew.
- Side effect: may flip `is_default=false` on a sibling BoatConfig (see Invariants).
- Downstream: BoatConfig slot count is the denominator for accepted-crew badges on schedule and regatta detail (`b4d60c6`, `2d6b8a7`); creating a new default mid-season changes those counts immediately.
- No websocket/event bus emission — clients must refetch.
- No audit log row written.

## External consumers
None known. Five direct UI dependents inside concorda-web (boat-positions-config form + preset buttons, dashboard inline-config-create flows). No mobile/Expo, scheduled job, or webhook usage observed.

## Open questions
- Should creating a new default config retroactively re-evaluate accepted-crew counts on already-published schedules, or only future ones? Today it's implicitly "immediate."
- `positions[]` has no server-side schema validation beyond `list[dict]` — should we enforce the `BoatConfigPosition` shape at the Pydantic layer to prevent silent drift?
- No cap on configs-per-boat; is that intentional?

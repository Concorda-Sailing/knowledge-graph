---
node_id: POST::/api/profile/boats/{0}/configs
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 698f356a910dbd24e6c46674b4b21e65cbb13ce07b61de34e41d11496208672d
status: llm_drafted
---

# POST /api/profile/boats/{boat_id}/configs

## Purpose

Creates a new crew configuration (BoatConfig) for a specific boat. This allows users to define preset crew structures (e.g., "Race Team" vs "Casual Crew") with specific position requirements. This endpoint is the primary way to expand the variety of available configurations beyond a single default.

## Invariants

- **Requires `boat_id` and `data` (BoatConfigCreate).**
- **Auth via `require_auth`** — the `current_user` must be authenticated.
- **Ownership check via `_require_boat_owner`** — the request will fail if the authenticated user does not own the boat.
- **Enforces single default** — if `is_default` is `True`, the method explicitly sets all other existing configurations for this `boat_id` to `is_default = False`.
- **Automatic `sort_order` assignment** — new configs are appended to the end of the list using the current `existing_count`.

## Gotchas

- **Single default enforcement** — per commit `09f19fa`, the logic must ensure only one configuration is marked as default per boat. If adding a new default, the previous default is unset via a bulk update.
- **Cascading side effects** — per commit `31aa70d`, changes to configurations (specifically `positions_needed`) may require cascading edits to `EventCrew` assignments and snapshots.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_boat_owner` to ensure only the boat owner can create configurations.
- **Side effects**: Changes to boat configurations may impact the visibility or structure of crew rosters in the `crew-roster service`.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.createBoatConfig`

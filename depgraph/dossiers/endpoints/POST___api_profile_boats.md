---
node_id: POST::/api/profile/boats
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4e4b1bd98eff1c88fcae0d936f74c6fc355f78ab7758bb9855a4b5c925a36cee
status: llm_drafted
---

# POST /api/profile/boats

## Purpose

Provides the API interface for managing a user's fleet of boats. This endpoint handles the creation, updating, and deletion of `Boat` records and manages the implicit relationship between the authenticated user and the boat (e.g., creating the `BoatCrew` record with the `owner` role upon creation). Use this when a user needs to modify their personal vessel registry or update vessel-specific metadata like sail numbers or dimensions.

## Invariants

- **POST `/boats`** requires `_require_boat_management` to pass, ensuring the user has the necessary permissions to add vessels to their profile.
- **POST `/boats`** creates a corresponding `BoatCrew` entry with `role="owner"` and `status="active"` for the `current_user`.
- **PUT `/boats/{boat_id}`** is restricted to a specific `BOAT_ALLOWED_FIELDS` whitelist; fields like `id` or `owner_id` cannot be modified via this endpoint.
- **PUT `/boats/{boat_id}`** requires the user to be the verified owner of the boat via the `_owner_query` check.
- **Returns `BoatRead`** schema for all successful operations.

## Gotchas

- **Reverted/Fixed Cascade Logic:** Per commit `31aa70d`, updates to `positions_needed` (part of the boat configuration) must cascade edits to the `positions_needed` snapshot and clear any orphan `EventCrew` assignments to prevent stale data.
- **Ownership Verification:** The `update_boat` method uses `_owner_query` to prevent IDOR attacks; if a user attempts to update a boat they do not own, the API returns a `403 FORBIDDEN`.
- **Conflict on Sail Number:** Creating a boat with an existing `sail_number` results in a `409 CONFLICT`.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes `_require_boat_management` for creation.
- **Websocket**: Emits `BOAT_UPDATED` event with the `boat.id` upon successful creation or update.
- **Side effects**: Updates to boat configuration (like `positions_needed`) impact the consistency of `EventCrew` assignments.

## External consumers

- `concorda-web` (via `profileApi.createBoat`)
- `concorda-test` (via `ApiClient.createBoat`)

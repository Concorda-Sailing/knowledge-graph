---
node_id: concorda-web::src/lib/api.ts::profileApi.updateBoatConfig
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 278116c54ee27d0ce9c38037fef7a34fc84c8a464188df8228ebaf7c98c8f500
status: llm_drafted
---

# profileApi.updateBoatConfig

## Purpose

Provides the API interface for managing a user's boat configurations (position sets). It allows for the retrieval, creation, updating, and deletion of specific configurations associated with a boat. This is distinct from `listCrewPools` or `getEventRegistrations`, as it specifically targets the spatial/positional configuration of a boat.

## Invariants

- **Method is `PUT`** — Updates to a configuration must use the `PUT` method to ensure the specific `configId` is targeted.
- **Requires `boatId` and `configId`** — Both identifiers are required in the URL path to target the specific resource.
- **Returns `BoatConfig`** — Successful updates return the updated configuration object.
- **Uses `fetchApiAuthenticated`** — All calls require a valid bearer token established via the authentication flow.

## Gotchas

- **Avoid shape-matching for IDs** — Per commit `bf15808`, the system was updated to use the stored `boat_config_id` explicitly rather than relying on matching the object shape; ensure updates target the specific ID to avoid mismatch errors.
- **Dependency on `BoatConfigUpdate` shape** — The `data` payload must strictly follow the `BoatConfigUpdate` type to avoid 400 errors during the `JSON.stringify` process in the `PUT` request.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the specific boat's configuration.
- **Side effects**: Updates to this endpoint directly affect the state of the `BoatPositionsConfig` and `ConfigForm` components in the boat management UI.

## External consumers

- `BoatPositionsConfig` (via `boat-positions-config.tsx`)
- `ConfigForm` (via `boat-positions-config.tsx`)

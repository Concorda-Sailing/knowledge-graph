---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteBoatConfig
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: db157d90b2ed352f1bdc968a017f2bedac7f374a464d0704e1d4e1bac195993a
status: llm_drafted
---

# profileApi.deleteBoatConfig

## Purpose

Removes a specific boat configuration from the user's profile. This is used when a user needs to strip specific settings or metadata associated with a boat's configuration. It is a specialized destructive action within the `profileApi` surface, distinct from `updateBoatConfig` (which modifies existing data) or `deleteCrewPool` (which manages group memberships).

## Invariants

- **HTTP Method is `DELETE`** — The request must use the DELETE verb to target the specific resource.
- **Requires `boatId` and `configId`** — Both identifiers are required to locate the specific configuration instance.
- **Uses `fetchApiAuthenticated`** — The call relies on a valid bearer token to authorize the deletion of user-specific configuration.
- **Returns a message string** — On success, the API returns an object with a `{ message: string }` shape.

## Gotchas

- **Dependency on `boat_config_id`** — Per commit `bf15808`, the system relies on stored `boat_config_id` values rather than shape-matching to identify configurations; ensure the UI is passing the correct ID and not an object or partial shape.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify their own profile configurations.
- **Side effects**: Deleting a configuration may impact the `BoatPositionsConfig` component in `boat-positions-config.tsx`.

## External consumers

- `concorda-web::src/components/boat/boat-positions-config.tsx::BoatPositionsConfig`

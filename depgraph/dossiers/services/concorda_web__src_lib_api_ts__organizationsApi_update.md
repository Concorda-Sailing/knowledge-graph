---
node_id: concorda-web::src/lib/api.ts::organizationsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a9c61eb19fdaff2f9952c5ee529450cd86cae36e181696c31624cad8de47c535
status: llm_drafted
---

# organizationsApi.update

## Purpose

Updates the metadata and configuration of an existing organization. It is used by administrative interfaces to modify organization-level details (like names or settings) via a `PUT` request. Use this instead of `create` when modifying an existing entity, and ensure the `id` matches the target organization.

## Invariants

- **Method is `PUT`** — Performs a full or partial update of the organization resource.
- **Requires an `id`** — The first argument must be the unique identifier for the organization being updated.
- **Returns the updated `Organization` object** — The response shape matches the `Organization` type, allowing for immediate UI state synchronization.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to authorize the request.

## Gotchas

- **Strict shape matching** — Per commit `bf15808`, ensure the payload respects the expected structure; recent changes to how IDs (like `boat_config_id`) are handled in the system suggest that mismatching shapes in the `update` body can lead to silent failures or incorrect data mapping.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires bearer token).
- **Side effects**: Updates to this node will affect the organization-level configuration visible in the `ClubEditPage` and `ClubDialog`.

## External consumers

None known.

---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteCrewPool
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 58b856dfdaa559ac5c503489ba23bb9920a2d5043bfbd0dad67dbb6c117171d1
status: llm_drafted
---

# profileApi.deleteCrewPool

## Purpose

Deletes a specific crew pool associated with a boat. This is a destructive operation used to remove a pool from a boat's profile. It is distinct from `updateCrewPool`, which modifies existing pool properties like name or membership.

## Invariants

- **HTTP method is `DELETE`**.
- **Requires two identifiers**: `boatId` and `poolId` to target the specific resource.
- **Returns a success message object** with the shape `{ message: string }`.
- **Uses `fetchApiAuthenticated`** to ensure the request is authorized via the user's session.

## Gotchas

- **Recent history shows tight coupling between boat configuration and display logic.** Commit `bf15808` fixed an issue where the system was using shape-matching instead of the explicit `boat_config_id`. When modifying or calling this method, ensure the `boatId` and `poolId` are correctly derived from the current boat context to avoid deleting the wrong resource.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi-authenticated` (requires valid user session).
- **Side effects**: Deleting a crew pool may affect the visibility of "accepting-crew" status on the regatta detail page and the schedule card (per commit `2d6b8a7`).

## External consumers

- `MyCrewTab` in `concorda-web` (via `my-crew-tab.tsx:181`).

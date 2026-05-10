---
node_id: concorda-web::src/lib/api.ts::boatApi.updatePunchlistItem
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 43d3b1d3b23f8e2bc16266e28b5cfa81a7243dc4dadd377da874e259ab8c4870
status: llm_drafted
---

# boatApi.updatePunchlistItem

## Purpose

Updates an existing item within a boat's punchlist. It performs a `PUT` request to the specific item endpoint to modify properties like `title`, `description`, `importance`, `status`, or `assigned_to_uuid`. Use this when a user is editing an existing task rather than creating a new one via `createPunchlistItem`.

## Invariants

- **Method is `PUT`** — This is an idempotent update of an existing resource.
- **Path structure** — Requires both `boatId` and `itemId` to target the specific resource: `/api/boats/${boatId}/punchlist/${itemId}`.
- **Auth requirement** — Uses `fetchApiAuthenticated` and requires a valid bearer token.
- **Return shape** — Returns the updated `PunchlistItem` object.

## Gotchas

- **`status` and `importance` are optional** — The `data` object allows for partial updates (e.g., updating only the `title` without affecting the `status`).
- **`assigned_to_uuid` dependency** — If updating the assignment, ensure the UUID is a valid user identifier to avoid backend validation errors.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Updates to the punchlist are intended to be reflected in the `BoatPunchlist` component.

## External consumers

- `BoatPunchlist` component in `concorda-web/src/components/boat/boat-punchlist.tsx`.

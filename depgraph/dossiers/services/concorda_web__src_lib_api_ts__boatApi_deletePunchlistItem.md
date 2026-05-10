---
node_id: concorda-web::src/lib/api.ts::boatApi.deletePunchlistItem
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 774394d1f51dbc88d259974b467d8f71fac3b746f90ec50759a7eeaf9fa2409c
status: current
---

# boatApi.deletePunchlistItem

## Purpose

Removes a specific item from a boat's punchlist via a `DELETE` request. It is the destructive counterpart to `updatePunchlistItem` and `addPunchlistItem` (implied by the `POST` pattern in the same block). An agent should use this when a user explicitly removes or strikes an item from the list rather than just updating its status.

## Invariants

- **HTTP Method is `DELETE`** — strictly follows RESTful patterns for resource removal.
- **Requires `boatId` and `itemId`** — both are required to target the specific resource path `/api/boats/${boatId}/punchlist/${itemId}`.
- **Returns a message object** — the expected response shape is `{ message: string }`.
- **Uses `fetchApiAuthenticated`** — the request must include the bearer token for authorization.

## Gotchas

- **Dependency on `boat_config_id`** — per commit `bf15808`, the system has moved toward using specific configuration IDs rather than shape-matching; ensure the `boatId` passed is the correct identifier for the current boat context to avoid 404s or targeting the wrong resource.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to modify the boat's punchlist.
- **Side effects**: Deleting an item here will trigger a re-render of the `BoatPunchlist` component in `concorda-web::src/components/boat/boat-punchlist.tsx`.

## External consumers

- None known.

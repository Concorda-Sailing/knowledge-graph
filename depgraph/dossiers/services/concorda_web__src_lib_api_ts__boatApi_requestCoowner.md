---
node_id: concorda-web::src/lib/api.ts::boatApi.requestCoowner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 465befe3e3a5969473950b28e9a24bafb4ef42758d7bfaaf596616cce1a6134c
status: current
---

# boatApi.requestCoowner

## Purpose

Triggers a request for co-ownership of a specific boat. This is a POST-based action used to initiate the transition of boat management rights. It is distinct from `coownerInvite`, which is used to send an invitation to a specific person or email; `requestCoowner` is the client-side trigger for the user to express intent to join a boat's management.

## Invariants

- **Method is POST** — Always uses the `POST` method to ensure the action is treated as a state-changing request.
- **Returns a specific shape** — Returns an object containing `{ request_id: string; boat_crew_uuid: string }`.
- **Requires a valid `boatId`** — The endpoint is scoped to a specific boat resource.
- **Uses `fetchApiAuthenticated`** — The request must be authenticated via the standard API client flow.

## Gotchas

- **Ownership requirements** — Per commit `47688ac`, the backend requires the user to have a "Boat Owner" membership to successfully process or interact with the co-owner invitation flow.
- **UX Flow dependency** — Per commit `eb382d2`, this call is part of a "directory-only invite dialog" flow; ensure the UI handles the transition from a request to an upgrade-prompt fallback if the user lacks sufficient permissions.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid bearer token).
- **Side effects**: Triggers updates to the co-owner invitation state, which affects the "incoming co-owner invites" display in the dashboard (per commit `e02996c`).

## External consumers

- `BoatFormInline` in `concorda-web::src/components/profile/boat-form-inline.tsx`.

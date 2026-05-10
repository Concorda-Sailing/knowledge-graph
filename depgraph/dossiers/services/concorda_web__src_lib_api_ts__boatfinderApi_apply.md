---
node_id: concorda-web::src/lib/api.ts::boatfinderApi.apply
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cfa9cf6990e5b975637c98f921c090ec996ef2e1b8dc2688a6cd08a4968ca011
status: current
---

# boatfinderApi.apply

## Purpose

Submits a membership application for a specific boat. It is a POST request to `/api/boatfinder/apply` that carries a user's message and the target `boat_id`. Use this when a user is transitioning from viewing a boat's profile to actively requesting to join/co-own that boat.

## Invariants

- **Method is `POST`** — unlike the sibling `getDetail` which is a GET request.
- **Requires `boatId` and `message`** — both are passed in the JSON body.
- **Returns a success message** — the response shape is `{ message: string }`.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to execute.

## Gotchas

- **Requires membership context** — per commit `47688ac`, the backend requires a "Boat Owner" membership to process certain invite/accept flows; ensure the user has the appropriate permissions before triggering the UI that calls this.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires bearer token).
- **Side effects**: Successful calls likely trigger notifications or status changes visible in the "directory-first invite UX" mentioned in commit `9e1cc53`.

## External consumers

- `concorda-web::src/app/members/boatfinder/apply-dialog.tsx` (via `ApplyDialog`)

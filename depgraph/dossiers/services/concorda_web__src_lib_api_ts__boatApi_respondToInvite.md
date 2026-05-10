---
node_id: concorda-web::src/lib/api.ts::boatApi.respondToInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 32a3164199f798827532364a68073b1d76b34f507d6aba6f074f9094f4c9e4fa
status: current
---

# boatApi.respondToInvite

## Purpose

Handles the formal acceptance or declination of a crew invitation for a specific boat. This method is used by the `BoatInviteView` to allow users to resolve pending invites. It is distinct from `inviteCrewBatch` or `resendInvite` as it is the terminal action for an invitee to change their status from pending to a resolved state.

## Invariants

- **HTTP Method is `PUT`** — The endpoint `/api/boats/${boatId}/crew-invite/respond` requires a `PUT` request.
- **Action is strictly typed** — The `action` parameter must be exactly `"accept"` or `"decline"`.
- **Returns a success message** — The response shape is `{ message: string }`.
- **Requires `fetchApiAuthenticated`** — The call must be authenticated to ensure the user has the right to respond to the invite.

## Gotchas

- **Requires Boat Owner membership for co-owner flows** — Per commit `47688ac`, the system now requires `Boat Owner` membership to successfully process certain invite-related transitions; ensure the user context is verified before calling this in UI flows.
- **Impacts status badges** — As seen in commit `2d6b8a7`, responding to an invite affects the "accepting-crew" status and count displayed on the regatta detail and schedule cards.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user is authorized to respond to the boat's invite.
- **Side effects**: Triggers updates to the "accepting-crew" status badge on regatta detail pages and the count on schedule cards.

## External consumers

None known.

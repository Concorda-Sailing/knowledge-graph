---
node_id: concorda-web::src/lib/api.ts::boatApi.coownerRemove
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3aa4304d3118c584a116d0cc64c491fcf706983a9c6c68c1d31f8f3c4471e014
status: current
---

# boatApi.coownerRemove

## Purpose

Removes a co-owner from a specific boat. It is a specialized administrative action within the `boatApi` service, distinct from `coownerInvite` which handles the addition of users. Use this when a user's access needs to be revoked from a boat's management tier.

## Invariants

- **HTTP Method is `POST`** — The endpoint expects a POST request to `/api/boats/${boatId}/coowner-remove`.
- **Requires `target_person_uuid`** — The request body must be a JSON object containing the specific person's UUID being removed.
- **Returns a `request_id`** — On success, the method returns an object containing a string `request_id` for tracking/logging.
- **Uses `fetchApiAuthenticated`** — This call is protected by the standard authentication layer and requires a valid bearer token.

## Gotchas

- **Membership requirement** — Per commit `47688ac`, the system requires the actor to have "Boat Owner" membership to successfully execute this removal. If the user is not a verified owner, the request will fail.
- **UI/UX dependency** — This method is directly called by `OwnersSection` in `owners-section.tsx:48`. Any changes to the signature or return shape will break the owner management view.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Affects the `OwnersSection` component visibility and user access levels for the specific boat.

## External consumers

None known.

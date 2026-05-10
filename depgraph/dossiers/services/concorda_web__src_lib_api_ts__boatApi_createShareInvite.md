---
node_id: concorda-web::src/lib/api.ts::boatApi.createShareInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3e0411ee621db509b8a06e4f26c928010f03511fdd05492fd9705afe98c9302f
status: current
---

# boatApi.createShareInvite

## Purpose

Generates a unique, single-use access token for a boat to allow external users to join the crew via a shared link. This is distinct from `inviteCrew`, which targets specific existing users via email or UUID; `createShareInvite` is intended for "public" or "semi-public" access where the identity of the joiner is not known upfront.

## Invariants

- **HTTP Method**: `POST` to `/api/boats/${boatId}/share-invite`.
- **Return Shape**: Returns an object containing a single string `token`.
- **Auth Requirement**: Uses `fetchApiAuthenticated`, requiring a valid bearer token from a user with sufficient permissions (typically Boat Owner or Admin).
- **Single-use Intent**: The resulting token is the mechanism used by `getShareInviteStatus` to track if a link has been `consumed`.

## Gotchas

- **Co-owner permissions**: Per commit `47688ac`, the backend requires Boat Owner membership to successfully interact with certain invite flows; ensure the caller has elevated privileges if this is used in a restricted context.
- **Status tracking**: The token returned is not just a string but a stateful object in the backend. Use `getShareInviteStatus` to check if the status is `"pending"` or `"consumed"` before attempting to use the token for joining-related logic.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` (Bearer token).
- **Side effects**: Successful consumption of a share invite typically triggers updates to the crew list and may affect the "accepting-crew" status visibility on regatta detail pages.

## External consumers

- `concorda-web::src/components/boat/boat-crew-invite.tsx` (BoatCrewInvite component).

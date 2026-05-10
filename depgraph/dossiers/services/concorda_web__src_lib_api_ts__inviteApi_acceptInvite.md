---
node_id: concorda-web::src/lib/api.ts::inviteApi.acceptInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c1fcbd027d2dc8f9fab9ce62767922f402649f0187bf2af7a6f009ff4498b48b
status: current
---

# inviteApi.acceptInvite

## Purpose

Finalizes a user's acceptance of a pending invitation via a POST request. It is used by the `InvitePageContent` component to transition a user from a "pending" state to an active member of a boat. Use this instead of `getInvite` when the user is ready to commit to the invitation.

## Invariants

- **Method is `POST`** — The endpoint `/api/invite/${token}/accept` requires a POST request to execute the acceptance.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the user's session is valid before processing the acceptance.
- **Returns success metadata** — Returns an object containing a `message` string and the `boat_uuid` of the associated boat.

## Gotchas

- **Role-based access requirements** — Per commit `47688ac`, accepting a "co-owner" invite requires the user to have a Boat Owner membership.
- **State synchronization** — Per commit `b4d60c6`, the system must track the delta between accepted invites and live slot counts; ensure the UI reflects the updated state immediately after this call to avoid stale "pending" indicators.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid bearer token).
- **Side effects**: Triggers updates to the user's `MembershipInfo` and may affect the "accepting-crew" status on regatta detail pages (per commit `2d6b8a7`).

## External consumers

- `concorda-web::src/app/invite/[token]/page.tsx` (via `InvitePageContent`)

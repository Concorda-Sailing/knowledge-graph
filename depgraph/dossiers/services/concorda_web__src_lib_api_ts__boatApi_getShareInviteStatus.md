---
node_id: concorda-web::src/lib/api.ts::boatApi.getShareInviteStatus
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0abf2e5a1ec8935e1a71aa5e9cc5a51af98d4a5272b80ca5fcaf8eb7f861bef5
status: current
---

# boatApi.getShareInviteStatus

## Purpose

Checks the current status of a boat's share invite using a specific token. It is used to determine if a visitor is viewing a "pending" invite or if the invite has already been "consumed" (e.g., the user has joined the boat). This is a distinct read-only check used to drive the UI state for the `BoatCrewInvite` component.

## Invariants

- **Requires `boatId` and `token`** — both must be provided to construct the URL.
- **Uses `encodeURIComponent` on the token** — ensures the token string does not break the URL structure.
- **Returns a status union** — the response shape is strictly `{ status: "pending" | "consumed" }`.
- **Authenticated request** — relies on `fetchApiAuthenticated` to provide the necessary bearer token.

## Gotchas

- **Status-driven UI logic** — per commit `2d6b8a7`, the status of these invites (and the resulting `EventCrewStatus`) drives the visibility of the "accepting-crew" badge on regatta detail pages.
- **Dependency on `BoatCrewInvite`** — this method is the primary data source for the `BoatCrewInvite` component (see `boat-crew-invite.tsx:104`).

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: The result of this check influences the "accepting-crew" status displayed on the regatta detail view.

## External consumers

None known.

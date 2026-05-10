---
node_id: concorda-web::src/lib/api.ts::boatApi.getPendingInvites
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1c1e7d87a0d2f95c48dcd5bf23932b55a31ce5b99d88e4a6b93bf377ad57f211
status: llm_drafted
---

# boatApi.getPendingInvites

## Purpose

Fetches the list of pending boat invitations for a specific boat. This is used to display incoming requests to a boat owner or administrator, allowing them to see who is waiting to join. It is distinct from `getCrew`, which returns established members, and `getVisibleCrew`, which returns a filtered view for public consumption.

## Invariants

- **Requires `boatId`** — The function accepts a single string argument representing the boat's unique identifier.
- **Authenticated request** — Uses `fetchApiAuthenticated` to ensure the caller has the necessary permissions to view boat-specific membership data.
- **Returns `PendingBoatInvite[]`** — The response is a typed array of invite objects.

## Gotchas

- **Relationship to co-owner invites** — Per commit `e02996c`, this endpoint is part of the flow that allows users to see incoming co-owner invites in the dashboard. Ensure any UI changes to "pending" states account for both standard crew invites and the co-owner upgrade path.
- **Status vs. Count** — Per commit `b4d60c6`, there is a distinction between counting accepted invites and the live slot count; when building UI components that rely on this data, ensure you are not conflating "pending" status with "active" membership.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Used to drive the "incoming co-owner invites" display in the dashboard.

## External consumers

None known.

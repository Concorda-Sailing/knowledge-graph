---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@334
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: da6acfa6eb3e83c48cddbacec3fb8166f3822629ea59d17ee00f5fbb1dc6830d
status: current
---

# Dan can send boat-level crew invites

## Purpose

Verifies that a co-owner (Dan) can successfully initiate a boat-level crew invite using a unique email address. This test ensures that the `inviteCrewByEmail` action correctly creates a `PendingCrewInvite` for an unrecognized email, rather than failing or attempting to attach to an existing `BoatCrew` record. It also validates that shared boat events created by a primary owner (Bob) are visible in the co-owner's (Dan) schedule UI after a manual session switch.

## Invariants

- **Email Uniqueness**: The test must use a fresh, timestamped email string to avoid collisions with existing `BoatCrew` rows, ensuring the target is a `PendingCrewInvite`.
- **Session Switching**: The UI test requires a manual `localStorage.setItem('auth_token', danToken)` injection to simulate the transition from the owner's session to the co-owner's session.
- **Visibility**: A boat-level event created by the owner must be visible on the `/members?tab=schedule` route for the co-owner.

## Gotchas

- **Unauth Redirects**: Per commit `ba1c3bd`, the test suite is sensitive to unauthenticated redirect targets; ensure the `page.goto('/')` and subsequent `localStorage` injection correctly maintain the session context to avoid being bounced to a login screen.
- **Race Conditions**: The UI assertion for `eventName` visibility uses a 10,000ms timeout to account for the `networkidle` wait and the time required for the `localStorage` injection to propagate through the app's auth state.

## Cross-cutting concerns

- **Auth**: Uses `danToken` (injected via `localStorage`) to simulate the co-owner's authenticated session.
- **Side effects**: Successful execution of `inviteCrewByEmail` creates a `PendingCrewInvite` record in the database.

## External consumers

None known.

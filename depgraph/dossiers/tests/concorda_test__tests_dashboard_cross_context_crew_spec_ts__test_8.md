---
node_id: concorda-test::tests/dashboard/cross-context-crew.spec.ts::test@8
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 23d29fbe44ce6fd8bcd218d99debf993da17408b23d7c2b5b08ebaea302807b8
status: current
---

# crew member sees the boat owner's boat in Boats tab

## Purpose

Verifies cross-context visibility for crew members, ensuring that when a user (Alice) is invited to a boat, she can see the boat in her "Boats" tab and the associated sailing events in her "Schedule." This test validates the end-to-end flow from owner-side invitation to invitee-side acceptance and UI rendering. It is distinct from single-user dashboard tests by requiring two distinct `ApiClient` sessions and manual `localStorage` manipulation to simulate the invitee's perspective.

## Invariants

- **Two-user orchestration**: Requires a successful `api.inviteCrewByEmail` from the owner (Bob) and a successful `api.respondToBoatCrewInvite` from the invitee (Alice).
- **State-driven UI**: The visibility of the boat card and the "Crew" badge is dependent on the successful acceptance of the invite.
- **Navigation-based identity**: The test uses `page.evaluate` to set the `auth_token` in `localStorage` to switch the browser context from the owner to the invitee.
- **Idempotent setup**: The setup steps (inviting and accepting) are designed to be idempotent to allow for retries in CI environments.

## Gotchas

- **Selector fragility**: Per commit `a7e3bd2`, the test must target the `Card` root or specific anchor patterns (`a[href*="boat="]`) to avoid failing when the UI structure changes.
- **Race condition/Duplicate handling**: Per commit `b57d89`, the test uses a `try/catch` block around `api.createSailingEvent` because the event name is fixed; if a previous run didn't clean up, the duplicate name error must be ignored to proceed.
- **URL-based navigation**: Per commit `be406a9`, the test must navigate specifically to the `?tab=boats` query parameter to ensure the correct view is rendered for the invitee.
- **Selector content-agnosticism**: Per commit `45c5b9b`, the schedule selectors must remain content-agnostic to avoid breaking when the `FIXED_EVENT_NAME` is used across multiple runs.

## Cross-cutting concerns

- **Auth**: Uses two distinct `ApiClient` instances (Bob and Alice) to simulate different user contexts.
- **Side effects**: Mutates the test database by creating a boat-crew relationship and a sailing event.

## External consumers

None known.

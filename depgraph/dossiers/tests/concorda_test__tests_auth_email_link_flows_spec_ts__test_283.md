---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@283
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 38b135bfdbe7df2b7c28954c42300b67f32fa3e62e9282fa2391022806aaa0a3
status: llm_drafted
---

# decline link flips BoatCrew status to declined

## Purpose

Verifies that clicking a "decline" link in an email invitation correctly updates the `BoatCrew` status. This test ensures that a user (e.g., Carol) can transition from a pending/invited state to a `declined` state via a hosted URL, and that this change is reflected in the backend `getBoatCrew` response. It validates the interaction between the email-generated decision URL and the underlying status transition logic.

## Invariants

- **URL Structure**: The decline URL must contain the pattern `/members/invite/decline/${crewId}`.
- **Identity Switching**: The test must explicitly switch between `bobToken` (the owner/sender) and `carolToken` (the recipient/invitee) to verify that the status change is visible to the correct parties.
- **Status Transition**: Upon successful navigation to the decline URL, the `BoatCrew` record for the user must reflect the status `'declined'`.
- **Cleanup Requirement**: The test must remove the crew member (if they are not an owner) to prevent side effects on subsequent tests in the suite.

## Gotchas

- **Order-dependent side effects**: Per the logic in `carolRequestsToCrew`, a prior test in the suite might have promoted the user to an active crew member via the dispatcher's UPSERT effect. This test requires a "defensive cleanup" to ensure the user is removed and the baseline is clean before proceeding.
- **Parallelism constraints**: This test is part of a `describe` block where `fullyParallel=false` is set in `playwright.config.ts`. The declaration order is critical because the tests rely on the specific state transitions (Accept vs. Decline) of the same user/boat entities.
- **Polling for status**: The status change is not instantaneous; the test uses a `.poll` mechanism on `api.getBoatCrew` to wait for the `'declined'` status to propagate.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken(bobToken)` to verify the owner's view and `setupRecipientSession(page, api, carolToken)` to simulate the invitee's interaction.
- **Side effects**: Directly affects the `BoatCrew` status, which is a dependency for the `getBoatCrew` API response.
- **Logic Source**: The behavior is driven by `_EventCrewHandler` in `services/invite_dispatch.py`, which handles the branching logic for the owner-side authorization path.

## External consumers

None known.

## Open questions

- Should the cleanup logic be moved into a global `afterEach` or a specialized `test.afterAll` to ensure the `BoatCrew` state is always reset, even if the test fails mid-execution?

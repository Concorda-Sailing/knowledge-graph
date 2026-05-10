---
node_id: concorda-test::tests/dashboard/cross-context-crew.spec.ts::test@51
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 627bf4c62acb70e799949f2ea611c9bcb1f2f141856e099acbcac6e87853cb80
status: llm_drafted
---

# crew member sees the race they were invited to in My Schedule

## Purpose

Verifies that a crew member (Alice) can see a specific sailing event in her "My Schedule" tab after being invited by a boat owner (Bob). This test validates the cross-context visibility of events that are not owned by the viewer but are shared via the crew pool. It ensures that the invitation-to-acceptance flow correctly propagates the event to the recipient's dashboard.

## Invariants

- **Uses a fixed event name** (`FIXED_EVENT_NAME`) to prevent the accumulation of unique event entries across multiple test runs.
- **Requires a two-step identity switch**: Bob (owner) creates/invites, then Alice (invitee) accepts.
- **Relies on `api.setToken`** to switch between `bobToken` and `aliceToken` for stateful API calls.
- **The UI assertion is the source of truth**: The test navigates to `/members?tab=schedule` and asserts the presence of the event text.

## Gotchas

- **Idempotency is required for stability**: Both `setEventCrewPool` and `respondToEventCrewInvite` must be wrapped in `try/catch` blocks or handled as idempotent calls because the test may fail/retry, leaving the event already created or the invite already accepted from a previous run.
- **Selector fragility**: Per commit `a7e8bd2`, the test must target the `Card` root rather than an anchor to avoid selection errors when navigating the dashboard.
- **Race condition on event creation**: The test uses a `try/catch` around `api.createSailingEvent` because if the `FIXED_EVENT_NAME` already exists from a previous failed run, the API will return an error. The test is designed to ignore this and proceed.

## Cross-cutting concerns

- **Auth**: Uses `ApiClient` to manage bearer tokens for two distinct users (`USERS.bob` and `USERS.alice`).
- **Side effects**: Successful execution populates the "My Schedule" tab for the invited user.

## External consumers

None known.

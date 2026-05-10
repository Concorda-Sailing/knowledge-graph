---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@346
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0657aaf9199a53af3b5a2b74a0147d01589dcf3c498288c7f25ecbc20ad87279
status: current
---

# UI: Dan sees the shared boat event on his schedule tab

## Purpose

Verifies that a sailing event created by a boat owner (Bob) is visible on the schedule tab of a co-owner (Dan). This test ensures that shared boat access correctly propagates event visibility across different user sessions, specifically testing the transition from a primary owner's context to a secondary user's context.

## Invariants

- **Requires two distinct identities**: A primary owner (Bob) to create the event and a co-owner (Dan) to view it.
- **Session switching via localStorage**: The test relies on manually injecting `danToken` into `localStorage` via `page.evaluate` to simulate the co-owner's authenticated session.
- **Event visibility is tied to boat access**: The event must be created on the specific `testBreezeId` to ensure it appears in the correct boat's context.

## Gotchas

- **Auth redirect behavior**: Per commit `ba1c3bd`, the test must ensure that the unauthenticated redirect target is correctly handled when switching sessions, or the test may fail during the `page.goto` transition.
- **Identity normalization**: The test relies on the "sole-owner-Bob normalization" logic (referenced in `ba1c3bd`) to ensure the event-creation context is consistent with the expected ownership model.

## Cross-cutting concerns

- **Auth**: Uses `danToken` and `localStorage.setItem('auth_token', ...)` to switch identity from Bob to Dan.
- **Side effects**: Verifies visibility on the `/members?tab=schedule` view.

## External consumers

None known.

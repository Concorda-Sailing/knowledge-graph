---
node_id: concorda-test::tests/events/browse-events.spec.ts::test@50
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3f8d5afdc84590d907331ef56749ed3313b9a8c08395aecd13029f755dfb0b84
status: current
---

# can navigate to event detail page

## Purpose

Verifies the navigation flow from the member events listing to a specific event's detail page. It ensures that the `EventsPage` abstraction correctly handles routing and that the event identity (e.g., `summer-series-2026`) is correctly resolved in the UI.

## Invariants

- **Uses `EventsPage` abstraction** — relies on the `gotoEvent` method to perform the navigation.
- **Requires successful authentication** — the test assumes the session is established prior to the `gotoEvent` call.
- **Expects visibility of event text** — the test passes only if the event name (regex `/summer series/i`) is visible within the 10s timeout.

## Gotchas

- **Selector fragility** — per commit `f552929`, selectors must be aligned with the actual UI to avoid test failure; ensure any changes to `EventsPage` methods or the underlying component structure are reflected in the test's `getByText` or `gotoEvent` logic.

## Cross-cutting concerns

- **Auth**: Relies on the authenticated state established in the global setup or preceding test blocks.
- **Side effects**: Verifies the visibility of the event detail view, which is a dependency for the event-driven navigation flow.

## External consumers

None known.

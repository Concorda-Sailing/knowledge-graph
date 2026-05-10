---
node_id: concorda-test::tests/events/browse-events.spec.ts::test@28
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e126628af98421114b00a5bdaafc81c457f3daf4cc3de75078c19d31f332fcbc
status: llm_drafted
---

# event card shows date and location

## Purpose

Verifies that event cards correctly display metadata (date and location) on the public events page. This test ensures that the `EventsPage` abstraction and the underlying UI components correctly render seeded data like "Boston Harbor" within the expected month accordions.

## Invariants

- **Requires month expansion.** The test must first click the month header (e.g., "July 2026") to make the event cards visible in the DOM.
- **Relies on seeded data.** The test expects specific text like "Boston Harbor" to be present, which is driven by the test data seeding.
- **Uses `EventsPage` abstraction.** All navigation and interaction must go through the `EventsPage` class rather than raw `page` commands to maintain consistency with the suite.

## Gotchas

- **Selector alignment.** Per commit `f552929`, selectors and visibility timeouts (e.g., `5_000` ms) were recently updated to align with the actual UI behavior to resolve failures in the initial green run.
- **Implicit dependency on month headers.** If the month header is not clicked first, the `getByText` locator for the location will fail to find the element, as the event is nested within a collapsed accordion.

## Cross-cutting concerns

- **Auth**: None (tests public event visibility).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.

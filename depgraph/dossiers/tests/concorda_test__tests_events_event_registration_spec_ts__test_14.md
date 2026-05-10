---
node_id: concorda-test::tests/events/event-registration.spec.ts::test@14
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4dc8c5b884791e00a0d84abedaa1c0c900c68e2320bc9860105d19525ab03a5f
status: llm_drafted
---

# ticket options are displayed

## Purpose

Verifies that the event detail page correctly renders ticket types and quantity controls for a specific event. It ensures that both "Skipper Entry" and "Crew Entry" options are visible and that the quantity increment button is functional. This test serves as a critical check for the event registration UI flow, distinguishing between general event visibility and specific ticket availability.

## Invariants

- **Requires `EventsPage` abstraction** — relies on `events.gotoEvent(slug)` to navigate to the correct event context.
- **Regex-based selection** — uses case-insensitive regex (e.g., `/skipper.*entry/i`) to locate ticket elements, allowing for minor text variations in the UI.
- **Network state dependency** — requires `page.waitForLoadState('networkidle')` to ensure ticket data has been fetched from the API before attempting to interact with buttons.
- **Timeout sensitivity** — uses explicit timeouts (5,000ms to 10,000ms) for visibility assertions to account for asynchronous loading of ticket components.

## Gotchas

- **Implicit dependency on event slug** — the test is hardcoded to `summer-series-2026`. If this event is removed from the seed data or the global setup, the test will fail during navigation.
- **Race condition in quantity increment** — the `page.waitForTimeout(500)` after clicking the `+` button is a manual delay to allow the state to settle; removing this or the `networkidle` wait may cause the test to fail on slower CI runners.

## Cross-cutting concerns

- **Auth**: Implicitly relies on the authenticated state established in the global setup to view/interact with specific event details.
- **Side effects**: Verifies the visibility of the registration UI which is a prerequisite for the actual registration flow.

## External consumers

None known.

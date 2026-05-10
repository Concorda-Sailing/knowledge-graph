---
node_id: concorda-test::tests/events/event-registration.spec.ts::test@26
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0539379a43849f5b6def797f0706683205d11990d06f481c666ecf6df32f33d6
status: current
---

# can select ticket quantity

## Purpose

Verifies that a user can interact with the ticket quantity selector on an event page. It specifically tests the ability to click the increment (`+`) button to increase the number of tickets selected before proceeding to checkout.

## Invariants

- **Requires `EventsPage` abstraction.** The test relies on `events.gotoEvent(slug)` to navigate to the correct event context.
- **Relies on `networkidle` state.** The test explicitly waits for `page.waitForLoadState('networkidle')` to ensure the ticket-loading component has finished fetching data before attempting to interact with the increment button.
- **Button interaction is conditional.** The test checks `isVisible()` for the `+` button before clicking, allowing the test to pass even if the quantity selector is not present or is disabled for certain event types.

## Gotchas

- **Race condition on button click.** The test uses a hardcoded `page.waitForTimeout(500)` after clicking the increment button. This is a fragile way to wait for the UI state to update and may lead to flaky results if the API response or component re-render takes longer than 500ms.
- **Initial commit scaffolding.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the test patterns here are still being established and may not yet follow the finalized interaction patterns of the broader suite.

## Cross-cutting concerns

- **Auth**: Implicitly depends on the user's session state; if the event is restricted, the `EventsPage` navigation may behave differently.
- **Side effects**: Interacts with the event registration flow, which may trigger state changes in the user's pending registration/cart.

## External consumers

None known.

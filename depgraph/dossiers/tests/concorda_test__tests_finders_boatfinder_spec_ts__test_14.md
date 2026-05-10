---
node_id: concorda-test::tests/finders/boatfinder.spec.ts::test@14
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4b37526075fd52e2185ea9d41223d25608acab8426496a67fa92d0bd48836fc0
status: current
---

# shows published boats accepting crew

## Purpose

Verifies the visibility and interaction of boat cards within the "Boatfinder" feature. It ensures that published boats (specifically "Test Breeze") are discoverable, display correct metadata (sail number, class), and that the navigation flow from the card to the detail view works as expected.

## Invariants

- **Requires `BoatfinderPage` fixture.** The test relies on the `BoatfinderPage` class to handle the initial `goto()` and navigation.
- **Expects specific text patterns.** Uses regex for "test breeze" and "apply/contact" to identify UI elements.
- **Navigation triggers `networkidle`.** The transition from boat card to detail view assumes a network-idle state to ensure the detail view has loaded before assertions.
- **Dialog interaction is asynchronous.** Clicking the "apply" button requires a `waitForTimeout(1000)` to allow the dialog to transition into the DOM.

## Gotchas

- **Sidebar IA dependency.** Per commit `cf4317c`, this spec was updated to accommodate the "new sidebar IA + unified finder." Changes to the sidebar navigation or the unified finder structure may break the `boatfinder.goto()` or the visibility of the boat cards.
- **Timeout sensitivity.** The "apply" button interaction uses a hardcoded `waitForTimeout(1000)`. If the environment is slow, the `messageInput` assertion may fail.

## Cross-cutting concerns

- **Auth**: None (assumes the user is already authenticated via the `BoatfinderPage` setup).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.

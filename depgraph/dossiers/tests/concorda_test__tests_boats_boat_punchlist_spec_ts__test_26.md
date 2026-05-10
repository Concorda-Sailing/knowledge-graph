---
node_id: concorda-test::tests/boats/boat-punchlist.spec.ts::test@26
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9e338643deee042293dd5f9bb778fe8d8749fde4d8d95585faf55866f4395456
status: current
---

# can create a punchlist item

## Purpose

Verifies the end-to-end lifecycle of a boat's punchlist, specifically the ability to create new items and transition existing item statuses. This test ensures that the UI components (tabs, buttons, and inputs) correctly interact with the underlying boat-specific state.

## Invariants

- **Requires a visible punchlist tab.** The test first verifies the presence of the `punchlistTab` before attempting interaction.
- **Uses regex-based selectors.** Selectors for buttons and inputs (e.g., `/add|new|create/i`) must remain flexible to accommodate minor UI text changes.
- **Relies on explicit timeouts.** The test uses `page.waitForTimeout(1000)` and `page.waitForLoadState('networkidle')` to account for asynchronous state updates in the UI.

## Gotchas

- **Fragile UI interaction.** The test uses `page.waitForTimeout(1000)` after clicking the "Add" button and "Save" button to allow for DOM stability; removing these or replacing them with faster assertions may lead to flakiness in the punchlist creation flow.
- **Selector ambiguity.** The status selection logic relies on `page.locator('select, [role="combobox"]').first()`, which assumes the punchlist item is the first interactive element in the list.

## Cross-cutting concerns

- **Auth**: Assumes an authenticated session is established prior to the test run (inherited from the test file's setup).
- **Side effects**: Successful creation of a punchlist item creates a new record in the database for the current boat.

## External consumers

None known.

---
node_id: concorda-test::tests/finders/boatfinder.spec.ts::test@42
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fe307c018c1ba1683ffffec4d9848d551ad05e8166cee7622d72e5da2ad1d000
status: llm_drafted
---

# apply button opens dialog

## Purpose

Verifies the "Apply" button interaction within the Boat Finder detail view. It ensures that clicking the button (labeled "Apply" or "Contact") successfully triggers the visibility of the message input field, confirming the transition from a read-only state to an active communication state.

## Invariants

- **Button selection is fuzzy.** The test looks for a button with the name `/apply|contact/i` to account for different UI states.
- **The message input is identified by placeholder or label.** It must match either `getByPlaceholder(/message/i)` or `getByLabel(/message/i)`.
- **Visibility timeout is strict.** The input must become visible within 3,000ms of the click.

## Gotchas

- **Requires explicit wait for UI transition.** The test uses `await page.waitForTimeout(1000)` after the click to allow the dialog animation/transition to complete before asserting visibility. Removing this or the timeout will cause flaky failures in CI environments.
- **IA dependency.** Per commit `cf4317c`, this test was updated to accommodate the "new sidebar IA + unified finder." Changes to the sidebar or the way the finder navigation is structured may break the ability to reach this button.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the boat detail view.
- **Side effects**: Verifies the entry point for the crew-request flow.

## External consumers

None known.

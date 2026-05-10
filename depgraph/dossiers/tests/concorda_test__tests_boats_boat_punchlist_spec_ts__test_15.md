---
node_id: concorda-test::tests/boats/boat-punchlist.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 973c859594cdb05762ead612ddd8ce212d5e69156a92279fd3fc3c95721798ad
status: current
---

# punchlist tab is accessible

## Purpose

Verifies the visibility and basic interactivity of the "Punchlist" tab within a boat's detail view. It ensures that users can navigate to the tab, verify the presence of task-related UI elements (like "add" buttons or status dropdowns), and perform basic CRUD-lite operations like creating a new item or changing a status.

## Invariants

- **Tab visibility is conditional.** The test uses `if (await punchlistTab.isVisible())` to wrap interactions, meaning the test may pass silently without actually asserting the tab's existence if the UI state is incorrect.
- **Uses regex for loose matching.** Selectors for tabs and buttons (e.g., `/punchlist/i`, `/add|new|create/i`) are designed to be resilient to minor text changes in the UI.
- **Relies on `networkidle`.** The setup assumes that clicking the boat tab triggers a network request that must settle before the punchlist tab becomes interactable.

## Gotchas

- **Implicit pass on missing UI.** Because the test wraps the core logic in `if (await ...isVisible())` blocks, a failure in the UI (e.g., the tab not appearing) results in a "green" test that did nothing, rather than a failure. This is a known pattern in this suite to handle non-deterministic loading states.
- **Hardcoded timeouts.** The test uses `await page.waitForTimeout(1000)` and `timeout: 5_000` in several places. These are brittle and rely on the local test environment's speed.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely established in a global setup or a preceding test in the same file) to access the boat detail view.
- **Side effects**: Creating a punchlist item via this test modifies the database state for the current test run.

## External consumers

None known.

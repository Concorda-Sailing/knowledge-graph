---
node_id: concorda-test::tests/boats/boat-punchlist.spec.ts::test@54
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1eca1bb19abc1eb833bcbe13fc2701668ff57288f97beccafa37f5b3af6f4c7f
status: current
---

# can change punchlist item status

## Purpose

Verifies the ability to update a punchlist item's status via the UI. It ensures that a user can navigate to the punchlist tab, locate a status dropdown (select or combobox), and successfully transition an item to an "In Progress" state.

## Invariants

- **Requires visibility of the `punchlist` tab** — the test uses a conditional check (`if (await punchlistTab.isVisible())`) to decide whether to proceed with the status change.
- **Targeting a status change** — the test specifically looks for a text match of `/in.*progress/i` to simulate a status transition.
- **Relies on `networkidle`** — the test waits for the network to be idle after clicking the tab to ensure the punchlist data has loaded before attempting to interact with the select element.

## Gotchas

- **Brittle selector dependency** — the test relies on `page.locator('select, [role="combobox"]').first()`. If the UI adds a different select element above the punchlist status, this test will likely fail or interact with the wrong element.
- **Implicit timing dependencies** — the test uses hardcoded `page.waitForTimeout(500)` and `page.waitForTimeout(1000)` to handle UI transitions. This is a sign of potential flakiness in CI environments if the component rendering is slower than the timeout.
- **Initial scaffolding state** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the test assumes a boat with an existing punchlist item is already present in the test state.

## Cross-cutting concerns

- **Auth**: Assumes the user is already authenticated via the setup/global-setup flow used in the `boat-punchlist.spec.ts` suite.
- **Side effects**: Updates the status of a punchlist item, which may trigger visibility changes in the boat's detail view or status badges.

## External consumers

None known.

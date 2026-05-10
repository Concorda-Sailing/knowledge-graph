---
node_id: concorda-test::tests/boats/boat-crud.spec.ts::test@29
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 95a0d579567a574cefdff92d04dae03baaa2e229dae09d8480f66ac0c8a9b7bb
status: current
---

# boat detail page shows boat info

## Purpose

Verifies that the boat detail page correctly renders information for a specific boat. It ensures that after navigating to the `/members` route, the UI displays the expected boat name and sail number (e.g., "Test Breeze" and "TEST-001") within the boat-specific tab.

## Invariants

- **Navigation path**: Must navigate to `/members` before attempting to interact with the boat tab.
- **Selector pattern**: Relies on a regex-based search for the boat name (`/Test Breeze/`) and sail number (`/TEST-001/`).
- **Visibility timeout**: Uses a 5,000ms timeout for the `toBeVisible` assertion to account for component mounting/loading.

## Gotchas

- **Conditional UI rendering**: The test uses `if (await boatTab.isVisible())` blocks. If the boat content fails to load or the tab is not present, the test may pass silently without actually asserting the detail view, masking a failure in the detail page rendering.
- **Race conditions**: The test relies on `page.waitForLoadState('networkidle')` and `page.waitForTimeout(1000)` to manage asynchronous UI transitions.

## Cross-cutting concerns

- **Auth**: Requires a valid authenticated session (likely established in a global setup or a prior `test.beforeEach` block) to access the `/members` route.
- **Side effects**: Verifies the visibility of data that is likely populated by the boat-related API endpoints.

## External consumers

None known.

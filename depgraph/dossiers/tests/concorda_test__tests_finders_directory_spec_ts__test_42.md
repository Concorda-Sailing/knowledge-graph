---
node_id: concorda-test::tests/finders/directory.spec.ts::test@42
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 984f77aefb16b65b4b47d41309551c32a067f6999630be9677822a09921bbe30
status: llm_drafted
---

# alphabet filter filters by last name

## Purpose

Verifies the alphabetical filtering logic within the Directory view. Specifically, it ensures that selecting a letter (e.g., 'M') correctly narrows the member list to display relevant results. This test is distinct from the "empty state" or "view toggle" tests in the same file, as it focuses on the data-driven filtering mechanism rather than UI layout or empty-state handling.

## Invariants

- **Alphabet filter must trigger a UI update.** The test relies on `directory.filterByLetter(char)` to successfully narrow the visible list.
- **Result visibility is checked via regex.** The test uses `page.getByText(/member/i)` to confirm that a matching record (e.g., "Alice Member") is visible after the filter is applied.
- **View toggle is independent of filter state.** The test verifies that switching between 'grid' and 'list' views does not break the component or cause errors.

## Gotchas

- **Hardcoded timeouts are required for stability.** The test uses `await page.waitForTimeout(1000)` after applying the filter and switching views. This suggests the directory component relies on asynchronous state updates or network latency that isn't immediately captured by Playwright's auto-waiting.
- **Initial commit scaffolding.** Per commit `fd0c570`, this suite is part of the initial E2E scaffolding; tests may be brittle or rely on specific test data (like "Alice Member") that must exist in the test environment.

## Cross-cutting concerns

- **Auth**: None (assumes directory access is granted via setup).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.

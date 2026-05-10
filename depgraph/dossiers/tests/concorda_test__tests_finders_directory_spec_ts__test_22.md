---
node_id: concorda-test::tests/finders/directory.spec.ts::test@22
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2e7c0a09a4767acaeccd5a64304ba34ecaa7c2a61f0c90e1c798f8eb20f173a9
status: current
---

# search by name works

## Purpose

Verifies the search functionality within the Member Directory. It ensures that the `directory.searchFor` helper correctly triggers name-based filtering and that the UI responds by displaying the expected member or an appropriate empty state.

## Invariants

- **Search triggers a UI update.** The test relies on `page.waitForTimeout(1000)` to allow the asynchronous search/filter operation to complete before asserting visibility.
- **Case-insensitivity.** The regex `/alice/i` in the assertion implies the search results should be resilient to casing in the UI.
- **Empty state handling.** The test expects the UI to show a "no results" message (e.g., "no members found") when a non-existent string is provided.

## Gotchas

- **Brittle timing.** The test uses hardcoded `page.waitForTimeout(1000)` (lines 24 and 32) to wait for search results. This is a fragile pattern; if the API or search debounce increases, these tests will fail.
- **Implicit view state.** The `view toggle works` test (lines 52-64) relies on the presence of both grid and list buttons. If the UI layout changes or the buttons are renamed, the test may skip the toggle logic entirely without failing.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely established in a higher-level `beforeEach` or `global-setup`) to access the `/members/directory` route.
- **Side effects**: Changes to the search implementation or the `directory` Page Object model will directly break this test.

## External consumers

None known.

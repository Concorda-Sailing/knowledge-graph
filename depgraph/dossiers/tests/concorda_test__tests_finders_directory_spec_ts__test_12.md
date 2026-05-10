---
node_id: concorda-test::tests/finders/directory.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b4971571e5b3fa88d5bebc4611a4df3c39b0616213b34a5741dfec7464cedb7c
status: llm_drafted
---

# directory page loads

## Purpose

Verifies the core functionality of the Member Directory page, including navigation, search, alphabetical filtering, and view toggling (Grid vs. List). This test ensures that the directory correctly displays opted-in members and handles empty search states without regressing the UI layout.

## Invariants

- **URL pattern**: The page must resolve to a URL matching the regex `/\/members\/directory/`.
- **Search behavior**: The `directory.searchFor` method must trigger a visible change in the member list.
- **View state**: Switching between 'grid' and 'list' buttons must not result in a page crash or broken layout.
- **Visibility**: Successful searches must result in elements being visible within a 5-10 second timeout.

## Gotchas

- **Manual timeouts required**: Tests frequently use `page.waitForTimeout(1000)` or `500` after interactions (e.g., `searchFor`, `filterByLetter`, or view toggles). This suggests the directory UI relies on asynchronous state updates or transitions that are not yet fully deterministic or covered by robust Playwright locators.
- **Regex-based text matching**: The test relies on loose regex for member names (e.g., `/alice|bob|carol|eve/i`) and "no results" states. If the UI text changes (e.g., "No members found" to "No results found"), these tests will fail.

## Cross-cutting concerns

- **Auth**: Implicitly requires a logged-in session to access the `/members/directory` route, though the specific guard is handled by the `DirectoryPage` setup.
- **Side effects**: Changes to the member directory (like opting in/out) will affect the visibility of members in this test.

## External consumers

None known.

---
node_id: concorda-test::pages/admin/clubs.page.ts::AdminClubsPage.searchFor
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 824943e00bae0eef6431e05a3944da6bee8f4237a6867ab21650c2c65d185f3a
status: llm_drafted
---

# AdminClubsPage.searchFor

## Purpose

The `searchFor` method simulates a user typing a search query into the club administration search input. It is used in E2E tests to filter the club list before performing actions like selecting a specific club or verifying a club's existence. It is distinct from `goto`, which handles navigation; `searchFor` specifically handles the interaction with the `searchInput` element.

## Invariants

- **Input is a raw string.** The method accepts a `query` and fills the input field directly.
- **Triggers a network idle state.** The method calls `await this.page.waitForLoadState('networkidle')` after filling the input to ensure the search-triggered API request has completed before the test proceeds.

## Gotchas

- **UI renames and copy changes break specs.** Per commit `9965eb9`, recent changes to the UI text and copy caused 4 specs to fail. When modifying the search input or the surrounding club list UI, ensure the test-side selectors and the expected text remain synchronized with the production changes.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `AdminClubsPage.goto`) to access the `/members/admin/clubs` route.
- **Side effects**: Filtering the club list via this method affects the visibility of club-specific action buttons (e.g., "Edit" or "Delete" buttons) in the subsequent DOM state.

## External consumers

None known.

---
node_id: concorda-test::pages/admin/users.page.ts::AdminUsersPage.searchFor
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 26e3915ec56edbddd6f9a955b9f7c6db11f587d469d315faa542a9fb2940b076
status: current
---

# AdminUsersPage.searchFor

## Purpose

The `searchFor` method simulates a user typing into the admin user search input to filter the user list. It is used in E2E tests to navigate to specific user profiles or to verify that search results correctly filter the table. Use this instead of manual `page.fill` calls to ensure the `networkidle` state is respected after the input is entered.

## Invariants

- **Input is a raw string.** The method accepts a `query` and injects it directly into the `searchInput` locator.
- **Triggers a network event.** Calling this method results in a `waitForLoadState('networkidle')` to ensure the search results have populated the UI before the test continues.
- **Requires prior navigation.** This method assumes `goto()` has been called to establish the `/members/admin/users` context.

## Gotchas

- **Selector sensitivity.** Per commit `f552929`, selectors must be kept in sync with the actual UI to avoid "first green run" failures. If the search input component changes, this method is a primary failure point.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session with admin privileges to access the `/members/admin/users` route.
- **Side effects**: Triggers the user list filtering/re-rendering in the Admin dashboard.

## External consumers

None known.

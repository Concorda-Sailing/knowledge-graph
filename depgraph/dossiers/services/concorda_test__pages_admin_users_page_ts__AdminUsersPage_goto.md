---
node_id: concorda-test::pages/admin/users.page.ts::AdminUsersPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ecc2cb09d02f4dc9ec5903e863bd205f0dec1f75859b7e270ebf52dcd37a9181
status: current
---

# AdminUsersPage.goto

## Purpose

Navigates the Playwright browser instance to the Admin User Management dashboard. It serves as the entry point for all E2E tests targeting user administration, such as password resets, user deletions, or profile updates.

## Invariants

- **Navigates to `/members/admin/users`** — the hardcoded path is the single source of truth for the admin user management route.
- **Waits for `networkidle`** — ensures the page and its underlying data-fetching (user lists, search results) are fully loaded before the test proceeds to interaction.

## Gotchas

- **Selector alignment required by commit `f552929`** — recent changes fixed issues where selectors were not matching the actual UI; ensure any new elements added to the Admin Users page are checked against the regex-based selectors (like `newPasswordInput` or `changePasswordSubmit`) to prevent brittle test failures.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session with admin privileges (typically established via `ApiClient.login` or a pre-set `storageState`) to access the `/members/admin/` route.
- **Side effects**: Changes made after calling `goto()` (like `searchFor` or password updates) directly impact the test database state for the user being edited.

## External consumers

None known.

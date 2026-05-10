---
node_id: concorda-test::pages/admin/clubs.page.ts::AdminClubsPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 75e9b0dcb9fbebeafb8571034c5dea2c0e44209bcdf1bc667fefca9e0bfb02e6
status: llm_drafted
---

# AdminClubsPage.goto

## Purpose

Navigates the Playwright browser instance to the Admin Clubs management dashboard. It serves as the entry point for all E2E tests targeting club-level administration, ensuring the page is fully loaded before subsequent interactions like `searchFor` or dialog manipulation.

## Invariants

- **Navigates to `/members/admin/clubs`**.
- **Waits for `networkidle`**. The method explicitly waits for the network to be idle to ensure that the club list and any initial data-fetching requests have completed before the test proceeds.
- **Requires an authenticated session.** This method assumes the browser context already has a valid session (likely via `ApiClient.login` or a `storageState` file) as it hits an `/admin/` protected route.

## Gotchas

- **UI Renames/Copy Changes.** Per commit `9965eb4`, this page is sensitive to UI text changes. Recent updates to labels or copy in the club management view have historically broken multiple specs in this suite.

## Cross-cutting concerns

- **Auth**: Requires an admin-level authenticated session/storage state to access the `/members/admin/` route.
- **Side effects**: Any test calling this method is part of the admin-side E2E suite; changes to the club management UI will directly impact the stability of these tests.

## External consumers

None known.

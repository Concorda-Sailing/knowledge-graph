---
node_id: concorda-test::pages/profile.page.ts::ProfilePage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d422614ae7234615bb39f82eb420047938bb2cb1a7e102b430e9bdac280634a8
status: llm_drafted
---

# ProfilePage.goto

## Purpose

Navigates the Playwright browser instance to the user profile settings page. It performs a two-step navigation: first navigating to the `/members` base path, then interacting with the UI to select the "Profile" tab. This is the standard entry point for tests requiring password changes or profile metadata updates.

## Invariants

- **Requires an active session.** The navigation assumes the user is already authenticated; if the session has expired or the user is not logged in, the `click()` on the profile tab will fail or redirect to a login flow.
- **Relies on `networkidle`.** The method waits for `networkidle` after the tab click to ensure the profile sub-route and its associated data-fetching are complete before returning control to the test.
- **Uses regex-based selectors.** The tab selection uses `/profile/i` to remain resilient against minor casing changes in the UI text.

## Gotchas

- **Initial commit scaffolding.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the navigation logic is currently hardcoded to a specific sequence (navigate to `/members` then click tab) which may be brittle if the dashboard routing structure changes.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session via `ApiClient` or similar setup before calling.
- **Side effects**: Used by tests that modify user credentials; changes made here affect the user's ability to authenticate in subsequent test steps.

## External consumers

None known.

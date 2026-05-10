---
node_id: concorda-test::pages/admin/system.page.ts::AdminSystemPage.gotoEmailConfig
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0b8fafd7aaa92bc2849cbb810ca9b1ca926b1a7269f053a434db977b35147fd3
status: llm_drafted
---

# AdminSystemPage.gotoEmailConfig

## Purpose

Navigates the Playwright browser instance directly to the Email Configuration sub-page within the admin dashboard. This is a specialized navigation helper for the `AdminSystemPage` class, used to bypass manual menu clicking when testing email-related settings.

## Invariants

- **Navigates to `/members/admin/email`** — the hardcoded path must remain valid for the admin routing structure.
- **Waits for `networkidle`** — ensures the page is fully loaded and any initial configuration fetches are complete before the test proceeds.
- **Requires an authenticated session** — the underlying `page` instance must already be authenticated as an admin to avoid redirects to the login page.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; ensure that any changes to the admin routing structure are reflected here, as this method relies on a static path.

## Cross-cutting concerns

- **Auth**: Requires an active admin session; navigation will fail or redirect if the user is not an admin.
- **Side effects**: Navigating here triggers the loading of email configuration settings, which may involve fetching provider-specific credentials or status from the API.

## External consumers

- `concorda-test::tests/admin/email-config.spec.ts`

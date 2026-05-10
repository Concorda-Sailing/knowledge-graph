---
node_id: concorda-test::pages/admin/events.page.ts::AdminEventsPage.gotoSeries
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0217baf8628e5364985ddbde095c46034e226c543f52442ae91a1d9ba4c31b4e
status: current
---

# AdminEventsPage.gotoSeries

## Purpose

Navigates the Playwright page instance to the Admin Series management view. This is a high-level navigation helper within the `AdminEventsPage` class used to transition the browser state before performing series-specific administrative actions. It is distinct from `gotoRaces` and `gotoSocials`, which target different sub-sections of the admin event management interface.

## Invariants

- **Navigates to `/members/admin/events/series`** via the Playwright `page.goto` method.
- **Waits for `networkidle`** to ensure the page is fully loaded and the API responses for the series list have settled before the test proceeds.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this file is part of the initial E2E suite scaffolding. The navigation paths and the `networkidle` wait-state are currently part of the baseline setup and may require updates if the admin routing structure changes.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely established via `ApiClient.login` or a similar setup) to access the `/members/admin/` route.
- **Side effects**: Navigating here resets the current view state of the admin dashboard.

## External consumers

- `concorda-test::tests/admin/event-management.spec.ts` (specifically used in test `@15`).

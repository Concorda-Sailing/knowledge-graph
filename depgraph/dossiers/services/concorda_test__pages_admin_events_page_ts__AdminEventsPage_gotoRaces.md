---
node_id: concorda-test::pages/admin/events.page.ts::AdminEventsPage.gotoRaces
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 50ea3ad2e680a9710707ad4dff4fbe7751f157585e1f807a68941b2581265ba0
status: current
---

# AdminEventsPage.gotoRaces

## Purpose

Navigates the Playwright browser instance to the administrative race management view. It is used to establish the correct URL context before performing CRUD operations on race-specific event data. It is distinct from `gotoSeries` or `gotoSocials`, which target different administrative sub-routes within the events module.

## Invariants

- **Navigates to `/members/admin/events/races`**.
- **Waits for `networkidle`** to ensure the administrative dashboard and any data-fetching sidecars have completed loading before the test proceeds.
- **Requires an authenticated session** via the `AdminEventsPage` instance to be useful; navigating here without a valid admin session will result in a redirect to login.

## Gotchas

- **Initial scaffolding only**: Per commit `fd0c570`, this file is part of the initial E2E suite scaffolding. The current implementation is a bare-bones navigation and does not yet include complex state-verification logic (like checking for a specific race list) that more mature pages might have.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session; navigation will fail or redirect if the session is invalid.
- **Side effects**: Navigating here triggers the loading of the race management dashboard, which may involve fetching race lists from the API.

## External consumers

- `concorda-test::tests/admin/event-management.spec.ts` (used in test setup/hooks).

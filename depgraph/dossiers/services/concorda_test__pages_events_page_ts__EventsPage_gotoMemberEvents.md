---
node_id: concorda-test::pages/events.page.ts::EventsPage.gotoMemberEvents
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a1335a99e3c5b7d73e7c52bb4bb0d31c0cdebd8cc288e2eb5238dde06328cc3
status: current
---

# EventsPage.gotoMemberEvents

## Purpose

Navigates the Playwright browser instance to the member-specific events view at `/members/events`. This is a high-level navigation helper used to transition the test state from a general landing page or login flow into the authenticated member dashboard context. It is distinct from `gotoPublicEvents`, which hits the unauthenticated `/events` route.

## Invariants

- **Navigates to `/members/events`** — the path is hardcoded and assumes a valid session is already established.
- **Waits for `networkidle`** — the method explicitly awaits the network to be idle after navigation to ensure the member-specific event list has loaded before the test proceeds to interaction.

## Gotchas

- **Requires prior authentication** — because this navigates to a `/members/` sub-route, it relies on the session established by `ApiClient.login` or `LoginPage.login`. If called without a valid session, the test will likely be redirected to a login page or receive a 401/403 error.
- **Initial scaffolding only** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; existing navigation patterns in this file are highly stable but may lack complex state-reset logic found in more mature pages.

## Cross-cutting concerns

- **Auth**: Requires an active session (likely via `ApiClient.login` or similar) to access the `/members/` route.
- **Side effects**: Navigating here resets the browser context to the member-specific view, affecting any subsequent assertions on the current URL or page state.

## External consumers

- `concorda-test::tests/events/browse-events.spec.ts` (used in test setup/navigation).

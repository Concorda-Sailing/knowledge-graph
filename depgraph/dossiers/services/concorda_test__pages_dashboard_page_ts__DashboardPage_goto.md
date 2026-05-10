---
node_id: concorda-test::pages/dashboard.page.ts::DashboardPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 64cee37c1b708c7e2d21bd0b0f2940635d9b9de2a20352387400cadf97bdb3e5
status: current
---

# DashboardPage.goto

## Purpose

The primary entry point for navigating to the user dashboard in E2E tests. It navigates the browser to the `/members` route and waits for the network to reach an idle state to ensure the page is ready for interaction. Use this instead of raw `page.goto` to ensure consistent setup for tests involving the dashboard, profile, or crew tabs.

## Invariants

- **Navigates to `/members`** — the base path for the dashboard view.
- **Waits for `networkidle`** — ensures all initial data fetching (crew, profile, etc.) is complete before the test proceeds.
- **Uses `this.page`** — relies on the underlying Playwright page instance provided during instantiation.

## Gotchas

- **Sidebar IA changes** — per commit `bdbd348`, this page was recently refreshed to accommodate new sidebar information architecture. If adding new navigation links, ensure they are registered in the constructor to avoid navigation failures.
- **Implicit dependency on `/members` route** — if the dashboard path changes in the web app, this method will fail.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (typically established via `ApiClient.login` or `storageState`) as the `/members` route is protected.
- **Side effects**: Navigating here triggers data fetching for the user's profile and crew-related components.

## External consumers

None known.

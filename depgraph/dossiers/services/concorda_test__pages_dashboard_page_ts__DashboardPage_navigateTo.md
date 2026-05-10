---
node_id: concorda-test::pages/dashboard.page.ts::DashboardPage.navigateTo
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b1fc23dad4a0ff98fefbf69218101f4bf8c63b7ff8ab804de0e12eda398a68ee
status: current
---

# DashboardPage.navigateTo

## Purpose

Provides a mechanism to navigate the dashboard via UI elements rather than direct URL manipulation. Unlike `goto()`, which forces a path, `navigateTo(link)` accepts a Playwright `Locator` to simulate clicking specific navigation elements (like sidebar links or tabs). This is the preferred method for testing flows that depend on the presence of a specific UI element to trigger a route change.

## Invariants

- **Requires a valid `Locator`** — the argument must be a clickable element (e.g., a sidebar link or a tab).
- **Triggers `networkidle`** — the method automatically waits for the network to be idle after the click to ensure the subsequent page/component has finished loading.
- **Simulates a single click** — it does not handle complex multi-step interactions; it is a single-action navigation helper.

## Gotchas

- **Recent IA changes** — per commit `bdbd348`, this method (and the `DashboardPage` class) was recently refreshed to accommodate a new sidebar Information Architecture. Ensure any `Locator` passed to `navigateTo` is compatible with the updated sidebar structure.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Navigation via this method triggers the loading of dashboard-specific components (e.g., the `userAvatar` or `myCrewTab` visibility states).

## External consumers

None known.

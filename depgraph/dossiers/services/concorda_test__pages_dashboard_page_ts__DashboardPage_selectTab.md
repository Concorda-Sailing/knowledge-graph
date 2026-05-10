---
node_id: concorda-test::pages/dashboard.page.ts::DashboardPage.selectTab
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3928e774bfc32171dc9c4cd2594ba5274f86cc678218e9f913f3e7d1f02ef908
status: llm_drafted
---

# DashboardPage.selectTab

## Purpose

The `selectTab` method performs a programmatic click on a specific navigation tab within the Dashboard view. It is used to navigate between different dashboard sections (e.g., switching from a high-level overview to a specific boat detail view). Use this instead of `hasTab` when you need to trigger the navigation event, and use it after ensuring the tab is visible to avoid Playwright click-intercept errors.

## Invariants

- **Input is a string or RegExp.** The `name` parameter must match the accessible name of the `role="tab"` element.
- **Requires visibility.** The method relies on `this.page.getByRole('tab', { name })` to locate the element; if the tab is not in the DOM or is hidden, the click will fail.
- **Triggers navigation/state change.** Calling this method is an action that changes the active view of the Dashboard.

## Gotchas

- **Sidebar IA changes.** Per commit `bdbd348`, this method (and the `DashboardPage` class) was recently updated to accommodate a new sidebar Information Architecture. Ensure any tab names passed to this method align with the updated sidebar structure to avoid "element not found" errors.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers view changes in the Dashboard, which may affect the visibility of sub-components like the boat-finder or event lists.

## External consumers

None known.

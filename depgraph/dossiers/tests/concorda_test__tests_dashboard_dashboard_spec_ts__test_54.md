---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@54
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7cd5dd36de63bff57282238d423b5227f844cd213f2ed8c5a433c2ae2b6c81e5
status: current
---

# clicking My Schedule tab shows schedule content

## Purpose

Verifies that the "My Schedule" tab in the user dashboard is functional and renders visible content. It ensures that when the tab is selected, the active `tabpanel` is not just present in the DOM, but has a non-zero height, distinguishing a rendered view from an empty or collapsed container.

## Invariants

- **Requires `dashboard.hasTab(/schedule/i)` check.** The test only executes the assertions if the schedule tab is actually present in the current UI context.
- **Expects a non-zero height.** The test explicitly asserts that the `tabpanel` bounding box height is greater than 20 pixels to ensure content is actually rendered.
- **Uses `page.waitForLoadState('networkidle')`** to ensure the tab transition and any subsequent data fetching are complete before checking visibility.

## Gotchas

- **Content-agnostic selector requirement.** Per commit `45c5b9b`, the test was updated to be content-agnostic; it checks for the existence of a `tabpanel` with `data-state="active"` rather than looking for specific text, to avoid fragility when the schedule data changes.
- **UI Alignment.** Recent history (commit `705f5bd` and `f5525929`) shows frequent adjustments to align selectors with the actual UI and the new sidebar IA. If the test fails, check if the `role="tabpanel"` or `data-state` attributes have changed in the component.

## Cross-cutting concerns

- **Auth**: Relies on the authenticated state established in the dashboard setup (likely via `ApiClient.login`).
- **Side effects**: Verifies the visibility of the schedule view, which is a primary feature of the user dashboard.

## External consumers

None known.

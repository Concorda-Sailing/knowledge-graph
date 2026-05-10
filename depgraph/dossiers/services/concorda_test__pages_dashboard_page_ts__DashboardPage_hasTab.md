---
node_id: concorda-test::pages/dashboard.page.ts::DashboardPage.hasTab
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b1f0473ff7cf6f843f4d3e3ffc4865c92081e0f5f039944b5eb90eaf6962966b
status: current
---

# DashboardPage.hasTab

## Purpose

The `hasTab` method is a conditional visibility check used to determine if a specific tab is present in the DOM. It is used primarily for testing features where tabs are rendered conditionally based on user permissions or data availability (e.g., boat-specific tabs). Use this to perform assertions before attempting to `selectTab`, preventing test failures when a tab is expected to be absent.

## Invariants

- **Input is a string or RegExp.** The method accepts either a literal name or a regular expression to match the tab's accessible name.
- **Returns a Promise resolving to a boolean.** It uses Playwright's `isVisible()` which checks if the element is both in the DOM and visible to the user.
- **Relies on ARIA roles.** It specifically looks for the `role="tab"` attribute.

## Gotchas

- **Sidebar IA changes.** Per commit `bdbd348`, the `DashboardPage` was recently refreshed to accommodate new sidebar Information Architecture; ensure any tab name passed to `hasTab` matches the updated navigation structure.

## Cross-cutting concerns

- **Auth**: Visibility of tabs is often tied to user permissions; if a user lacks access to a specific resource, `hasTab` will return `false`.
- **Side effects**: Used to gate interactions in tests that depend on the presence of specific dashboard modules.

## External consumers

None known.

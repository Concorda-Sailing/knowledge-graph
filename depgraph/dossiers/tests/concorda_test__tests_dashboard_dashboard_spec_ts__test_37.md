---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@37
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e954f80316f45e6b0587071793123c49bb537f08309c8de615dbf6186b2d5260
status: current
---

# dashboard has tab navigation

## Purpose

Verifies the presence and basic functionality of the dashboard tab navigation system. It ensures that the user can switch between the "Schedule" and "Profile" tabs and that the corresponding content panels are not only visible but also rendered with non-zero dimensions. This test acts as a high-level smoke test for the dashboard's internal routing and state management.

## Invariants

- **Tab existence is conditional.** The test uses `dashboard.hasTab()` to check for the existence of tabs before attempting to select them, preventing failures if a specific user role lacks access to a tab.
- **Content must have physical presence.** For the "Schedule" tab, the test asserts that the `tabpanel` has a bounding box height greater than 20px to ensure it isn't just an empty, zero-height container.
- **Requires `networkidle`.** The test explicitly waits for `page.waitForLoadState('networkidle')` after selecting a tab to ensure the component has finished fetching data before asserting visibility.

## Gotchas

- **Selector fragility.** Per commit `f552929`, selectors must be aligned with the actual UI and the setup must be correctly configured for the first green run. 
- **Content-agnosticism.** Per commit `45c5b9b`, the test relies on the fact that selectors are content-agnostic (e.g., checking for a `tabpanel` or a generic text pattern) to avoid breaking when specific schedule or profile data changes.
- **UI Alignment.** Commit `705f5bd` indicates this suite requires frequent alignment with the current UI on the test host to prevent regressions in the dashboard layout.

## Cross-cutting concerns

- **Auth**: Depends on the `dashboard` fixture, which requires a valid authenticated session (likely established via `api.login` in a parent test or global setup).
- **Side effects**: Verifies the visibility of the "Schedule" and "Profile" views, which are core components of the user dashboard.

## External consumers

None known.

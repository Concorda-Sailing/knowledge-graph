---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@32
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 322338dcd7a0017f9fe075f39ab62a65c436c56fa5ff942f299db64b2bf0e8cb
status: llm_drafted
---

# member directory link navigates correctly

## Purpose

Verifies that the Member Directory link in the dashboard correctly navigates the user to the `/members/directory` route. This test ensures that the primary navigation path for user-facing directory information remains intact following sidebar IA changes.

## Invariants

- **Navigation target is absolute**: The test expects the URL to match `/\/members\/directory/` exactly.
- **Dashboard fixture dependency**: Relies on the `dashboard` fixture to provide the `directoryLink` locator.
- **Clickability**: The `directoryLink` must be an actionable element (not obscured or disabled) to pass the navigation assertion.

## Gotchas

- **Sidebar IA sensitivity**: Recent changes to the sidebar structure (see commit `cf4317c`) have altered how links are discovered. Ensure the `dashboard.directoryLink` locator remains compatible with the updated navigation hierarchy.
- **Navigation timing**: The test relies on a direct `.click()` followed by a URL assertion; if the application introduces heavy client-side routing transitions, this may require an explicit `waitForURL` or `waitForLoadState`.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session via the `dashboard` fixture to access the directory route.
- **Side effects**: Navigation to the directory may trigger data fetching for member lists; ensure the test environment has seeded directory data if visibility of the resulting page is later asserted.

## External consumers

None known.

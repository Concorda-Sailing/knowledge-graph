---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@27
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1ba3320d9eddacc1d17232df23477c84eb6ce543357465a7e80bf127a883d9b9
status: current
---

# finder link navigates to unified finder page

## Purpose

Verifies the navigation logic for the unified "Finder" page and the "Member Directory" link. It ensures that the sidebar links correctly redirect the user to the expected URL paths (`/members/finder` and `/members/directory`) and validates that the dashboard's tab-based navigation (Schedule and Profile) is functional and renders visible content.

## Invariants

- **URL patterns must match routing**: The "Finder" link must resolve to a path matching `/\/members\/finder(\?.*)?$/` to account for potential query parameters.
- **Tab visibility**: The `profile` and `schedule` tabs must be detectable via regex and must render a non-empty `tabpanel` (height > 20px) to pass.
- **Sidebar IA**: The test expects the "Crew & Boat Finder" link to be present, while "Crew Finder" and "Boat Finder" must be absent (count 0).

## Gotchas

- **Sidebar IA Regression**: Per commit `cf552929`, the sidebar structure was recently updated to a "unified finder" model. Tests must assert that the old separate "Crew Finder" and "Boat Finder" links are removed to prevent regressions in the Information Architecture.
- **Content-agnostic tab testing**: As noted in commit `45c5b9b`, the schedule selectors are designed to be content-agnostic. The test checks for the existence of a `tabpanel` and a minimum height rather than specific data to avoid brittle failures when the schedule is empty.

## Cross-cutting concerns

- **Auth**: Relies on the authenticated state established in the `dashboard.spec.ts` setup (likely via `ApiClient.login`).
- **Side effects**: Changes to the routing structure of the `/members/` paths will break this test.

## External consumers

None known.

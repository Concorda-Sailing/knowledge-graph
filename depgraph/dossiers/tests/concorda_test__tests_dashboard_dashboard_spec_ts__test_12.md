---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e2d2c49f194d4400ef0ce1976e863b5a9d74ada99449c4d096f798c4ce89f3ab
status: llm_drafted
---

# dashboard loads with sidebar navigation

## Purpose

Verifies the core layout and navigation of the user dashboard. It ensures the sidebar is visible, contains the correct high-level navigation links (Dashboard, Finder, Directory), and that tabbed navigation (Schedule, Profile) functions correctly. This test acts as a regression guard for the primary user landing experience.

## Invariants

- **Sidebar presence is mandatory.** The `dashboard.sidebar` must be visible before any navigation attempts.
- **Navigation links must be specific.** The test expects the "Crew & Boat Finder" link to exist, while older, deprecated links like "Crew Finder" or "My Schedule" must have a count of 0.
- **Tabbed content must render height.** For the "My Schedule" tab, the test asserts that the active `tabpanel` has a bounding box height greater than 20px to ensure it isn't just an empty container.
- **Navigation is URL-driven.** Clicking the Finder link must result in a URL change to `/\/members\/finder(\?.*)?$/`.

## Gotchas

- **Sidebar IA changes.** Recent commits `cf4531c` and `705f5bd` indicate this suite is highly sensitive to Information Architecture (IA) changes. If the sidebar structure or link names change, this test will fail.
- **Selector fragility.** Per commit `f552929`, selectors must be aligned with the actual UI to avoid "first green run" failures.
- **Content-agnosticism.** The "Schedule" tab test is designed to be content-agnostic; it checks for the presence of a rendered panel rather than specific data to avoid brittle failures when the schedule is empty.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (via `DashboardPage.goto()`) to access the dashboard.
- **Side effects**: Changes to the sidebar navigation or the unified finder page will break this test.

## External consumers

None known.

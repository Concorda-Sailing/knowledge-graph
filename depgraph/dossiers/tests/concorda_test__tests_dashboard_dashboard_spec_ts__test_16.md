---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@16
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c389310914b3319fdf2ef4bf87e7b4242eddf8c36a6a2ee4787f2d6c1c8789b6
status: current
---

# sidebar contains main navigation links

## Purpose

Verifies the structural integrity and navigation of the main dashboard sidebar and tab system. It ensures that the primary navigation links (Dashboard, Crew & Boat Finder, and Directory) are present and that the unified finder and profile/schedule tabs function as expected. This test acts as a regression guard for the Information Architecture (IA) of the dashboard.

## Invariants

- **Sidebar links must follow the new IA.** Links like `crew finder`, `boat finder`, and `my schedule` must have a count of 0 to ensure the old, deprecated navigation items are removed.
- **Navigation must be functional.** Clicking the `crew & boat finder` link must result in a URL change to the `/members/finder` path.
- **Tab rendering must be non-empty.** When switching to the `schedule` tab, the active `tabpanel` must not only be visible but must have a height greater than 20px to ensure it isn't an empty container.

## Gotchas

- **IA Regression.** Per commit `cf552929`, the sidebar was recently updated with a new IA. Tests must explicitly check that old links (e.g., `crew finder`, `boat finder`, `my schedule`) are no longer present to prevent accidental re-introduction of deprecated navigation paths.
- **Selector Fragility.** Per commit `f552929`, selectors were updated to align with the actual UI. Use of generic text-based selectors (e.g., `getByRole('link', { name: /.../i })`) is preferred over strict string matching to accommodate minor text variations in the UI.

## Cross-cutting concerns

- **Auth**: Relies on the `DashboardPage` setup, which assumes a valid authenticated session is established via the global setup/`ApiClient` flow.
- **Side effects**: Validates the visibility of the `crew & boat finder` and `directory` links, which are the primary entry points for user-facing dashboard features.

## External consumers

None known.

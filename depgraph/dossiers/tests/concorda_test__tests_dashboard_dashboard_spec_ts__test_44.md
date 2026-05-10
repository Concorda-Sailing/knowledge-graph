---
node_id: concorda-test::tests/dashboard/dashboard.spec.ts::test@44
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fee9c868c93912f78b33d753250aa1e66a3e023315ed79434d390fcfab0212ac
status: llm_drafted
---

# clicking My Profile tab loads profile content

## Purpose

Verifies the tab navigation functionality within the user dashboard. It ensures that the "My Profile" and "My Schedule" tabs are not only present but also functional and capable of rendering their respective content panels. This test acts as a regression guard for the dashboard's information architecture (IA) and tab-switching logic.

## Invariants

- **Tab visibility is conditional.** Tests check for the existence of tabs (e.g., `dashboard.hasTab(/profile/i)`) before attempting to select them to prevent failures in environments where specific tabs might be hidden.
- **Content must have physical presence.** The "My Schedule" test requires the active `tabpanel` to have a bounding box height greater than 20px to ensure it is not an empty or zero-height container.
- **Requires `networkidle`.** The test relies on `page.waitForLoadState('networkidle')` to ensure the component has finished fetching data and rendering before asserting visibility of profile or schedule content.

## Gotchas

- **Selector fragility.** Recent history shows frequent updates to align with UI changes (e.g., commit `f552929` and `cf4317c`). Selectors for tabs and content must be content-agnostic or use regex to avoid breaking during IA shifts.
- **Tab panel height.** A simple visibility check is insufficient for the schedule tab; per the test logic, the `tabpanel` must have a non-null bounding box and a height `> 20` to pass.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the dashboard and profile views.
- **Side effects**: Changes to the dashboard sidebar IA or tab structure (as seen in `cf4317c`) will directly break this test.

## External consumers

None known.

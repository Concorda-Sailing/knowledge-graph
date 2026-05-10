---
node_id: concorda-test::tests/events/event-schedule.spec.ts::test@68
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d18b5640b06028ed1a65cb1290499481d872033acab42511ddc0c0718b949e7
status: current
---

# fresh event with no plan and no crew → auto edit mode

## Purpose

Verifies the automatic transition between "Edit Mode" and "View Mode" on the event schedule page based on the presence of logistics and crew data. It ensures that a fresh event defaults to an editable state, but once logistics (like dock time) are populated, the UI shifts to a view-only state to prevent accidental modifications.

## Invariants

- **Auth via LocalStorage**: The test manually injects the `bobToken` into `localStorage` via `page.evaluate` to simulate a logged-in session for the Playwright browser context.
- **Cleanup via `finally` block**: Every test uses a `try...finally` pattern to ensure `api.removeScheduleEvent(event.id)` is called, preventing orphaned event data in the test database.
- **View Mode Signal**: The presence of an "Edit" button (via `expectViewMode`) is the primary indicator that the UI has successfully transitioned out of auto-edit mode.

## Gotchas

- **Inverted Logic Requirement**: Per commit `97cbd50`, the test must explicitly check for "View Mode" when logistics are present. Previously, the expectation was inverted; the test now ensures that populating logistics triggers the transition from auto-edit to view mode.
- **Selector Fragility**: Per commit `ea0f908`, the test relies on the "Cancel" button or the "Edit" button as a signal for mode state. If the UI changes the text of these buttons, the `expectViewMode` and `expectEditMode` helpers will fail.
- **Race Conditions in Setup**: The test relies on `api.createSailingEvent` and `api.upsertSailingEvent` to establish the state before the page load. If the API response is slow, the `page.goto` might trigger before the backend has finalized the record.

## Cross-cutting concerns

- **Auth**: Uses `api.login` with `USERS.bob` credentials and requires `api.setToken` to establish identity.
- **Side effects**: Creates and deletes `SailingEvent` records in the test database.

## External consumers

None known.

---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@45
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8dbf551fcb400eb6a83a4b8daed49710602e395eeb3d71151da1a805d139d0bb
status: llm_drafted
---

# add event button navigates to form

## Purpose

Verifies the end-to-end flow of creating a new social event via the Admin dashboard. It ensures the "Add Event" button is visible, correctly navigates to the creation form, and successfully persists a new event with at least one ticket type. This test is a critical path for administrative event creation and ensures the UI-to-API-to-DB loop is intact for the social events feature.

## Invariants

- **Navigation path**: The test must navigate to `/members/admin/events/new` via the `addEventButton` to reach the creation form.
- **Form requirements**: A valid event creation requires at least one name field (`#event-name`) and one ticket type (name and price).
- **URL pattern**: The creation form is identified by the regex `/\/members\/admin\/events\/new/`.
- **Visibility**: The "Add Event" button must be visible within a 5-second timeout before interaction.

## Gotchas

- **UI Alignment**: Recent changes in `7e8363c` and `f552929` indicate that selectors and setup are highly sensitive to the current web UI state (e.g., the removal of inner profile Tabs). Ensure any changes to the `AdminEventsPage` class or the underlying component structure are reflected here to avoid brittle failures.
- **Timing/Race Conditions**: The test relies on explicit `waitForTimeout` calls (e.g., 1000ms after ticket creation, 2000ms after event creation) to allow the UI to settle. If the API or network latency increases, these hardcoded waits may cause flaky failures in the event list view.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely established via `ApiClient.login` in a global setup or parent test block).
- **Side effects**: Successful execution creates a real event record in the test database, which may affect the visibility of events in the "Socials" list view for subsequent tests.

## External consumers

None known.

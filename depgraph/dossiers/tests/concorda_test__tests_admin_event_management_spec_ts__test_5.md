---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@5
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 55b01cd771b20ed550b125f38a55125d7965b20e4be6af15ce5e033e036e8347
status: current
---

# races page loads

## Purpose

Verifies the core navigation and creation workflows for Admin event types (Races, Series, and Socials). It ensures that the `AdminEventsPage` can successfully navigate to specific event category views and that the "Add Event" flow—including the multi-step process of adding a name, date, and ticket type—is functional. This test is a critical gate for the admin-side event lifecycle.

## Invariants

- **URL patterns must match category routes**: Races must resolve to `/members/admin/events/races`, Series to `/members/admin/events/series`, and Socials to `/members/admin/events/socials`.
- **The "Add Event" flow requires a ticket**: Creating an event is not complete until at least one ticket type (e.g., "General Admission") is added via the UI.
- **Form field visibility**: The `#event-name` and `#event-date` inputs must be visible and interactable before the form is considered valid for submission.

## Gotchas

- **Selector fragility**: Recent changes in the web UI (specifically the removal of inner profile Tabs) required adjustments to the E2E suite to prevent breakage (see commit `7e8363c`).
- **UI Alignment**: Selectors must be strictly aligned with the current web UI components to avoid the "first green run" failures seen in earlier development (see commit `f552929`).

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session; assumes the `AdminEventsPage` is accessed via a user with elevated permissions.
- **Side effects**: Successful creation of an event via the "can create a new event" test will persist a new event record in the test database, potentially affecting the visibility of events in the `AdminEventsPage` list for subsequent tests if not cleaned up.

## External consumers

None known.

---
node_id: concorda-test::tests/events/event-schedule.spec.ts::test@128
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6750128a73496727c67585cfbc655c912ef9825c07b38c652ea572610cb89c9d
status: llm_drafted
---

# event with logistics and crew set up → view mode

## Purpose

Verifies that a sailing event with both logistics (dock time/location) and a defined crew pool defaults to "view mode" rather than "edit mode." This test ensures that when a user (in this case, `bob`) accesses the schedule tab for a specific event, the UI correctly identifies the event as fully configured and presents the read-only view.

## Invariants

- **Requires a valid `bobToken`** via `api.login(USERS.bob.email, USERS.bob.password)`.
- **Requires a `boat_uuid`** associated with the user's crew to successfully create the event.
- **Must include `dock_time` and `departure_location`** via `api.upsertSailingEvent` to trigger the "fully set up" state.
- **Must set a crew pool** via `api.setEventCrewPool` containing the current user's ID to satisfy the view-mode condition.
- **Cleanup is mandatory**: The `finally` block must call `api.removeScheduleEvent(event.id)` to prevent state leakage between test runs.

## Gotchas

- **UI State Transition**: Per commit `97cbd50`, the expectation was recently inverted; this test specifically validates that adding logistics and crew moves the UI from an "auto-edit" state into "view mode."
- **Selector Fragility**: Per commit `f552929`, selectors in this suite are content-agnostic to avoid failures when event names are dynamically generated with `Date.now()`.
- **Cleanup Failure**: If `api.removeScheduleEvent` fails or is skipped, subsequent tests in the suite may encounter unexpected event counts or state conflicts.

## Cross-cutting concerns

- **Auth**: Uses `api.login` to establish identity and `localStorage.setItem('auth_token', ...)` to inject the token into the Playwright browser context.
- **Side effects**: Creates and deletes a `SailingEvent` in the test database; failure to clean up affects the `event-schedule` test suite stability.

## External consumers

None known.

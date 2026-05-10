---
node_id: concorda-test::tests/events/event-schedule.spec.ts::test@94
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8687a6dbf4ee45f54071b1e9a35da76a17c79cb047f39856adeaa551d968d79b
status: llm_drafted
---

# event with logistics filled but no crew → view mode

## Purpose

Verifies that the event detail page defaults to "view mode" when logistics (dock time, location) are populated but no crew has been assigned. This test ensures that the UI doesn't prematurely trigger an edit-mode state just because logistics are present, and that the user must explicitly interact with the Crew card to enter edit mode.

## Invariants

- **Requires `api.upsertSailingEvent`** to set `dock_time` and `departure_location` to satisfy the "logistics filled" condition.
- **Uses `localStorage.setItem('auth_token', ...)`** to inject the `bobToken` into the browser context so the page loads in an authenticated state.
- **Relies on `expectViewMode(page)`** to assert that the UI remains in a non-editable state despite the presence of event data.
- **Cleanup is mandatory** via `api.removeScheduleEvent(event.id)` in a `finally` block to prevent test pollution.

## Gotchas

- **Auto-edit logic was recently inverted.** Per commit `97cbd50`, the expectation for "logistics-only" events was changed to ensure the page defaults to view mode rather than auto-entering an edit state.
- **Order of operations matters for "set up" status.** To test the "crew set up" state, the test must call `api.setEventCrewPool(event.id, [bobMe.id])` after the initial event creation and logistics upsert.

## Cross-cutting concerns

- **Auth**: Uses `api.login` with `USERS.bob` and injects the token via `localStorage` to bypass manual login UI steps.
- **Side effects**: The test creates a transient sailing event that must be cleaned up via `api.removeScheduleEvent` to avoid cluttering the event list for subsequent tests.

## External consumers

None known.

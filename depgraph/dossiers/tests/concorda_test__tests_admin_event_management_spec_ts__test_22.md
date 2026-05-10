---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@22
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 12fe09fe5b73c3a1f1384d3b0da435dd3f4c1706a2f84699ff2fbeb079770c09
status: llm_drafted
---

# socials page loads

## Purpose

Verifies that the "Socials" page within the Admin Events dashboard loads correctly and allows for the creation of new events. This test ensures that the navigation to the socials-specific view works, the "Add Event" button is present, and the multi-step form (including ticket creation) successfully persists a new event to the database and reflects it in the UI.

## Invariants

- **Navigation target**: The test expects a redirect to `/\/members\/admin\/events\/socials/` when calling `gotoSocials()`.
- **Form requirements**: Creating an event requires a name (`#event-name`), a start date (`#event-date`), and at least one ticket with a name and price.
- **UI State**: The "Add Event" button must be visible and functional to reach the creation form.
- **Persistence check**: A successful creation must result in the new event being visible in the list after a page navigation/refresh.

## Gotchas

- **Selector alignment**: Recent changes in `commit f552929` and `commit 7e8363c` were required to align selectors with the actual web UI and fix setup issues for the first green run.
- **Implicit timeouts**: The test relies on `page.waitForTimeout(2000)` and `page.waitForTimeout(1000)` to handle asynchronous state updates during the event creation flow; removing these or shortening them may lead to flaky failures in the event list visibility check.
- **Form interaction order**: The ticket creation flow requires clicking the "Add Ticket" button and waiting for `#ticket-name` to become visible before filling, or the test will fail.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (likely established via `ApiClient.login` in a global setup or preceding test).
- **Side effects**: Creating an event via this test mutates the test database, affecting the visibility of events in the admin dashboard and any related list views.

## External consumers

None known.

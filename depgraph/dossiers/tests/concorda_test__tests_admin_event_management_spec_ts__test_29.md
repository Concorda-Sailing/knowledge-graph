---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@29
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ce1459e5577b4951843feecbe717d7c1919638f60daa5c2670b754db46f67483
status: llm_drafted
---

# seeded events appear in list

## Purpose

Verifies the end-to-end flow of creating a new "Social" event via the Admin dashboard. It ensures that the "Add Event" button correctly navigates to the creation form, handles the required ticket-type sub-form, and that the newly created event is immediately visible in the "Socials" list view.

## Invariants

- **Requires a "Social" category event** — The test relies on the existence of a seeded event (e.g., "Summer Series") to verify the list rendering works.
- **Mandatory fields** — A valid event creation requires both a name (`#event-name`) and a start date (`#event-date`), plus at least one ticket type.
- **Navigation is URL-driven** — The test expects a redirect to `/\/members\/admin\/events\/new/` upon clicking the add button.
- **Post-creation redirect** — The application must redirect the user back to the admin events list after a successful creation.

## Gotchas

- **Selector alignment** — Recent commits `7e8363c` and `f552929` indicate that selectors (like the Add Event button and form fields) frequently drift from the actual UI. Always verify that `AdminEventsPage` methods and local selectors like `#event-name` match the current DOM.
- **Timing-sensitive visibility** — The test uses `waitForTimeout(2000)` and `waitForTimeout(1000)` to handle state transitions between ticket creation and event submission. These are brittle; if the test fails on CI, check if the `waitForSelector` or `waitForURL` calls need more robust assertions.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely established via `api.login` or `storageState` in a global setup).
- **Side effects**: Creates a new event record in the database; ensure the test environment is reset or uses unique names to avoid collisions in persistent test environments.

## External consumers

None known.

---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@59
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 149ccb023a33414ce2ec64dec93d802d1a6200c8aa29f72342fd012df5498380
status: llm_drafted
---

# can create a new event

## Purpose

Verifies the end-to-end flow for creating a new "Social Event" via the admin dashboard. It ensures that an administrator can navigate from the event list to the creation form, populate required fields (Name, Date, and at least one Ticket Type), and successfully persist the event to the database.

## Invariants

- **Requires a multi-step form interaction**: The test must click the "Add Event" button, fill the event name and date, and explicitly add a ticket type before the "Create Event" button becomes functional.
- **Uses `AdminEventsPage` abstraction**: Relies on the `AdminEventsPage` POM to handle navigation to the `/members/admin/events/new` route.
- **Persistence Verification**: The test concludes by navigating back to the "Socials" view to confirm the new event is visible in the list, ensuring the write-to-read cycle is complete.

## Gotchas

- **Selector Fragility**: Recent changes in the UI require precise interaction. Per commit `f552929`, selectors must be aligned with the actual UI components (e.g., ensuring the ticket name and price fields are visible and interactable) to avoid test failures during the setup phase.
- **Implicit Wait Requirements**: The test uses `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` to account for asynchronous state updates in the UI after clicking "Create Ticket" and navigating back to the list. Removing these without replacing them with robust `expect(locator).toBeVisible()` calls may lead to flakiness.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (likely established via `api.login` in a global setup or preceding test).
- **Side effects**: Successful execution creates a new event record in the database, which will appear in the admin event list and any dependent dashboard views.

## External consumers

None known.

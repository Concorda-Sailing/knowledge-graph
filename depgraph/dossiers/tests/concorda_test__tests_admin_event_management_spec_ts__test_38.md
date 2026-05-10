---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@38
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6939c6706d4c37c0fe313df2b2ecef4da05b2662bf83a9108aaa8e89d1358b46
status: llm_drafted
---

# add event button is present

## Purpose

Verifies the end-to-end flow of creating a new event via the Admin "Socials" view. It ensures that the "Add Event" button correctly navigates to the creation form and that a fully populated event (including a required ticket type) is successfully persisted and subsequently visible in the list.

## Invariants

- **Navigation path**: The flow must navigate from `AdminEventsPage.gotoSocials()` to the `/members/admin/events/new` URL pattern.
- **Required fields**: A successful creation requires an `#event-name`, an `#event-date` (ISO format), and at least one ticket with a `#ticket-name` and `#ticket-price`.
- **Visibility**: The test relies on the `AdminEventsPage.addEventButton` being visible before interaction.

## Gotchas

- **Selector Fragility**: Recent history shows frequent adjustments to align with the actual Web UI. Per commit `f552929`, selectors must be strictly aligned with the current UI components to avoid failures during the "first green run."
- **Race Conditions**: The test uses `page.waitForTimeout(2000)` and `page.waitForTimeout(1000)` to handle asynchronous state updates after clicking "Create Event" and "Create Ticket." Removing these or shortening them may cause the test to fail to find the newly created event in the list.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (established via `AdminEventsPage` setup).
- **Side effects**: Creates a new event record in the database; if run against a persistent environment, this increases the count of "Social" category events.

## External consumers

None known.

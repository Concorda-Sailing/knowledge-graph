---
node_id: concorda-test::tests/api/schedule-crew-options-gating.spec.ts::test@201
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a58bccff96c5be71bf9ef88b153de6f131f1ba244301f27eb3ce186ab9a0d261
status: llm_drafted
---

# crew-mode bookmark surfaces crew_boats (regression guard)

## Purpose

This test ensures that when a user is in "crew mode" (having no active captain bookmark for a specific regatta), the schedule item correctly surfaces the `crew_boats` array. This is a regression guard to ensure that the `crew_boats` data (representing the boat the user is looking to join/ride) is visible to the viewer, even when they are not the captain of the event.

## Invariants

- **Role transition is one-way**: `addRegattasToSchedule` upgrades a user from crew to captain, but it cannot downgrade a captain back to crew.
- **Fresh state requirement**: To test the "crew" state, the test must explicitly call `removeScheduleEvent` to clear any existing captain-mode bookmarks.
- **`crew_boats` visibility**: In crew mode, the `item.crew_boats` array must contain the `boat_id` of the person they are looking to ride with (e.g., `danBoatId`).

## Gotchas

- **State cleanup is mandatory**: Because `addRegattasToSchedule` only upgrades and never downgrades, you must call `bob.removeScheduleEvent(regattaEventId)` before attempting to set up a crew-mode bookmark. Failing to do this will cause the test to fail because the user will remain in captain mode.
- **Regression against `.first()` selection**: This test defends against the `.first()-without-order_by` bug where a schedule card might incorrectly surface the captain's boat instead of the crew's target boat.
- **Recent fix requirement**: Per commit `cc05a2a`, this test specifically asserts that `crew_boats` are hidden when in captain-mode, but must be present when in crew-mode.

## Cross-cutting concerns

- **Auth**: Uses `bob` (user instance) to perform `listMySchedule` and `addRegattasToSchedule`.
- **Side effects**: Modifies the schedule state for the user, which affects the `ScheduleItem` returned by the API.

## External consumers

None known.

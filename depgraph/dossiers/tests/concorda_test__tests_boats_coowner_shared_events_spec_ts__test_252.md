---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@252
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7f9d028a4a3e37162b64c32b7dbd4c48d502ad86e97911bfc12e6ca74a42edde
status: current
---

# Bob modifies the event; the change is visible to Dan

## Purpose

Verifies that modifications made by a co-owner (Bob) to a shared sailing event are immediately visible to the primary owner (Dan). This test ensures that state synchronization works correctly across different user identities when one user updates the logistics (arrival location, dock time) of an event created by another.

## Invariants

- **Event identity persistence**: The `event.id` must remain constant through the `upsertSailingEvent` call to ensure the update targets the correct record.
- **Data integrity**: Updates to `arrival_location` and `dock_time` must be reflected in the owner's view of the same event.
- **Temporal consistency**: Uses `futureDate(42)` to ensure the event exists in the future relative to the test execution time.

## Gotchas

- **Deletion permissions**: Per the logic in the `Dan (co-owner) can remove a shared event` test, a co-owner can successfully call `removeScheduleEvent(eventId)` to delete a shared event, which subsequently deletes the boat's involvement and potentially the Event itself if no other schedules remain.
- **Identity-based visibility**: The test relies on the fact that `dan.listMySchedule()` correctly surfaces events created by `bob` when they are linked via the shared `testBreezeId`.

## Cross-cutting concerns

- **Auth**: Requires authenticated `dan` and `bob` instances with appropriate permissions to modify shared boat events.
- **Side effects**: Successful deletion via `removeScheduleEvent` triggers the removal of the event from both the co-owner's and the primary owner's schedules.

## External consumers

None known.

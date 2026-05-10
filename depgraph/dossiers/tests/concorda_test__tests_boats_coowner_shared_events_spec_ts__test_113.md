---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@113
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 416d256481d18cceb44b8f306e8945b31800cc24092ccf02a6ecd3966679ef61
status: llm_drafted
---

# custom event Bob creates on Test Breeze appears on Dan's schedule

## Purpose

Verifies that events created by a boat owner (Bob) appear correctly on the schedule of a co-owner (Dan). It ensures that the `viewer_role` is correctly identified as `boat_co_owner` for the co-owner, distinguishing them from the primary owner or a standard invitee. This test is critical for ensuring that co-ownership provides visibility into the schedule without granting the same implicit permissions as a primary owner.

## Invariants

- **`viewer_role` must be `boat_co_owner`** — When Dan views an event created by Bob on a boat they co-own, the `ScheduleItem` must explicitly carry this role to allow the UI to render the distinct visual card.
- **Event visibility** — Events created by the owner (Bob) must appear in the co-owner's (Dan) schedule via `listMySchedule()`.
- **Regatta attachment** — Attaching a regatta to a boat (via `addRegattasToSchedule`) must propagate that event to the co-owner's schedule.

## Gotchas

- **Co-owners are no longer auto-accepted** — Per commit `0990b5d` and the logic in lines 163-183, a previous bug caused co-owners to be silently auto-accepted into crew pools. The current implementation ensures that if a co-owner is "invited," they receive a standard invite that can be declined, rather than being automatically added to the event.
- **Manual skip for missing seed data** — If no upcoming regatta is found in the test environment, the test skips via `test.skip(true, ...)` (line 142) to avoid false negatives caused by empty test-host state.

## Cross-cutting concerns

- **Auth**: Uses `dan` and `bob` identities (likely `ApiClient` instances) to simulate different user permissions and visibility.
- **Side effects**: Successful execution of these tests validates the logic used by the "schedule detail page" to render the `viewer_role` badge.

## External consumers

None known.

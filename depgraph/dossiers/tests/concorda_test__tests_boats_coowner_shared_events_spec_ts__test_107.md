---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@107
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ab4cda0bb3009eca0c32e891fec74aa40a77ac865b507e6c70bdae5889cee3e7
status: current
---

# Dan is confirmed as co-owner of Test Breeze

## Purpose

Verifies that a boat co-owner (Dan) can see events created by the primary owner (Bob) on the shared boat's schedule. It ensures that while the co-owner sees the event with a specific `viewer_role` of `boat_co_owner`, the event remains distinct from the owner's own events. This test validates the visibility logic for shared resources and ensures that co-ownership provides visibility without unintended auto-acceptance of invites.

## Invariants

- **`viewer_role` distinction**: When a co-owner views an event created by the owner, the `viewer_role` must be explicitly set to `'boat_co_owner'`.
- **Owner visibility**: The event creator (the owner) sees the event in their schedule without a special `viewer_role` tag.
- **Cleanup requirement**: Any event created during the test must be tracked in `createdEventIds` and removed via `removeScheduleEvent` in the `afterAll` block to prevent state leakage.

## Gotchas

- **Auto-acceptance regression**: Per commit `ba1c3bd`, co-owners used to be silently auto-accepted into events if they were boat owners. This test ensures that co-owners now receive a standard invite that they must explicitly accept/decline, rather than being automatically added to the crew.
- **Regatta seeding dependency**: The test involving regattas (lines 136-161) will skip if no upcoming regatta is currently seeded on the test host. This is a common failure point in CI environments if the seed data is stale.

## Cross-cutting concerns

- **Auth**: Uses `dan` and `bob` (ApiClient instances) to simulate two distinct authenticated users with different permission levels (Owner vs. Co-owner).
- **Side effects**: Successful execution of `bob.addRegattasToSchedule` and `bob.createSailingEvent` mutates the test database state; `afterAll` is used to clean up these specific IDs.

## External consumers

None known.

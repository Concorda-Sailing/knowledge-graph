---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@136
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 21ba6529c3d1713eee5f7427dced4b11099dd038cb7aa4ae2735720b7dcf956a
status: current
---

# regatta Bob attaches to Test Breeze appears on Dan's schedule

## Purpose

Verifies the visibility and role-assignment logic for boat co-owners when participating in sailing events. It ensures that a regatta added to a boat's schedule is visible to both the owner and the co-owner, while correctly distinguishing between a "crew" role and a "boat_co_owner" role. This test prevents regressions where co-owners might be incorrectly flagged as crew or where event visibility is lost during role transitions.

## Invariants

- **Regatta visibility**: A regatta added to a boat's schedule via `addRegattasToSchedule` must appear in the `listMySchedule` results for both the owner and the co-owner.
- **Role distinction**: A co-owner viewing an event they are invited to should see `viewer_role: 'boat_co_owner'` (or `null` if the specific badge logic applies) rather than a standard `crew` status.
- **Event lifecycle**: The test relies on `upcoming.id` being valid; if no upcoming regatta is seeded, the test skips via `test.skip(true)`.

## Gotchas

- **Auto-acceptance regression**: Per commit `ba1c3bd`, previously, boat owners/co-owners were being silently auto-accepted into events. The fix ensures that while the inviter auto-accepts, co-owners receive a standard `invited` status so they can explicitly decline if they are double-booked.
- **Badge logic**: As noted in the source comments, a co-owner who is also part of the `EventCrew` will see `viewer_role: null` (no badge) because the "Crew" badge is reserved for those not owning/co-owning the boat.

## Cross-cutting concerns

- **Auth**: Uses `bob.listMySchedule()` and `dan.listMySchedule()` which rely on the authenticated `ApiClient` state for the respective users.
- **Side effects**: `createdEventIds` is used to track and cleanup events created during the test to prevent state leakage in the test database.

## External consumers

None known.

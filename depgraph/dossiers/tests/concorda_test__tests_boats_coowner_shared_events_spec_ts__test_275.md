---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@275
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: de62b28f7e80e94310a7dcb9213aa0b6d985c2c14e9a603706c60b56f3daf00c
status: llm_drafted
---

# Dan can send event crew invites for the shared boat event

## Purpose

Verifies that a co-owner (Dan) can manage crew invites and lifecycle events for a shared boat event. This test ensures that when a co-owner interacts with an event created by another user (Bob), they have the necessary permissions to invite crew members and, crucially, to remove the event from both their own and the original creator's schedule.

## Invariants

- **Co-owner permissions**: A user with co-owner status must be able to call `setEventCrewPool` and `sendEventCrewInvites` on events they did not create.
- **Event removal**: Calling `removeScheduleEvent` on a shared event must result in the event being removed from both the creator's (`bob`) and the co-owner's (`dan`) schedules.
- **Crew role assignment**: When a user is invited to an event they do not own, their `viewer_role` must be set to `'crew'`.
- **Email-based invites**: The `inviteCrewByEmail` method must successfully create a `PendingCrewInvite` when using a unique email address.

## Gotchas

- **Pre-fix 404 error**: Previously, attempting to delete a shared event via `DELETE /my-schedule/events/{id}` resulted in a 404 because the co-owner lacked a personal bookmark or copy. This was fixed by the co-owner path implementation (see commit `ba1c3bd`).
- **Email uniqueness**: `inviteCrewByEmail` requires a fresh email (e.g., using `Date.now()`) to avoid no-op collisions against existing `BoatCrew` rows.

## Cross-cutting concerns

- **Auth**: Uses `dan` and `bob` `ApiClient` instances to simulate different user identities and permission levels.
- **Side effects**: Successful removal of a shared event deletes the associated Sailing Event (SE) and the user's involvement in it.

## External consumers

None known.

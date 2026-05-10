---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@302
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b5f0a7626f5cd4efee86e79ff7962fd6fd2ea1065c6738cd573326b5d7ddd26e
status: llm_drafted
---

# Dan (co-owner) can remove a shared event Bob created

## Purpose

Verifies that a co-owner (Dan) has the authority to remove a shared event created by another user (Bob). This test ensures that the `DELETE /my-schedule/events/{id}` endpoint correctly handles the co-owner permission path, allowing them to tear down the shared event (SE) and, if no other SEs remain, the underlying Event itself.

## Invariants

- **Co-owner deletion is destructive** — Removing a shared event via `dan.removeScheduleEvent(eventId)` must result in the event being removed from both the creator's (Bob) and the co-owner's (Dan) schedules.
- **Requires a valid event context** — The event must be created via `bob.createSailingEvent` to ensure the co-owner has a valid target to manipulate.
- **Success implies removal** — After a successful deletion, `listMySchedule()` for both the creator and the co-owner must return `undefined` for that specific `eventId`.

## Gotchas

- **Pre-fix 404 behavior** — Per the source comment, prior to the co-owner path implementation, this operation would return a 404 because the user lacked a personal bookmark or copy. This test specifically guards against that regression.
- **Email uniqueness for invites** — When testing `inviteCrewByEmail`, a fresh email (using `Date.now()`) is required to avoid collisions with existing `PendingCrewInvite` rows, which would make the test a no-op.

## Cross-cutting concerns

- **Auth**: Uses `dan.removeScheduleEvent` and `dan.inviteCrewByEmail`, relying on the co-owner's authenticated session.
- **Side effects**: Deleting a shared event via this path can trigger the deletion of the parent `Event` if no other shared events remain for that boat.

## External consumers

None known.

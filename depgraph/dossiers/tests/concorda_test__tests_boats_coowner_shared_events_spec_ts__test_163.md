---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@163
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a7e21b1e3782485da9e0b7e06e38a15d74267e5078f8f7848857c36e3abf9eed
status: llm_drafted
---

# Co-owner Dan is invited (not auto-accepted) when Bob sends a crew invite

## Purpose

Verifies that boat co-owners are not automatically accepted into events when invited, ensuring they must explicitly respond to an invite. This distinguishes between the "inviter" (who auto-accepts) and the "co-owner" (who receives a pending invite). This test ensures that co-owners can still decline an event to avoid double-booking, preserving the distinction between boat ownership and active crew status.

## Invariants

- **Co-owners receive an `invited` status** rather than `accepted` when a crew invite is sent.
- **The inviter (owner) auto-accepts themselves** when they are part of the crew pool.
- **The `viewer_role` is `null`** for co-owners on the schedule view, even if they are not part of the `EventCrew` row, to prevent the "Crew" badge from appearing.
- **The event remains visible on the co-owner's schedule** even before they accept the invite.

## Gotchas

- **Regression: Co-owners used to be silently auto-accepted.** Per commit `0990b5d`, a fix was required because previously, co-owners were being auto-accepted because they were boat owners of the event's boat. This allowed users to be double-booked without a formal invitation/decline step.
- **The "Crew" badge logic:** A co-owner with no `EventCrew` row will see `viewer_role: null`. If they are invited and accept, they gain the row, but the "Crew" badge is still suppressed because they are a boat owner.

## Cross-cutting concerns

- **Auth**: Uses `bob` (inviter) and `dan` (co-owner) identities to test permission-based state transitions.
- **Side effects**: Affects the visibility of the `viewer_role` and `status` on the `my-schedule` view and the `EventCrew` table.

## External consumers

None known.

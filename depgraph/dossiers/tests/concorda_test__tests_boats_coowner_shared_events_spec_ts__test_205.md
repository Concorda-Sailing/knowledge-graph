---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@205
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d74f1492cdf5a08cfa6149a9452b0d99c27c19deda7db92c7898d6c35864f940
status: current
---

# Inviter auto-accepts themselves (Bob inviting Bob stays accepted)

## Purpose

Verifies the "auto-accept" behavior of a boat owner when they invite themselves to an event. It ensures that if a user (Bob) creates an event and then invites themselves (or is already part of the crew pool), their status remains `accepted` rather than transitioning to a pending state. This test is critical for ensuring that co-owners do not lose access to events they are actively managing.

## Invariants

- **Self-invitation results in `accepted` status.** The user who creates the event or is already in the crew pool must not be stuck in a `pending` state after a `sendEventCrewInvites` call.
- **Edits are bidirectional.** Changes made by one co-owner (e.g., `upsertSailingEvent` for `departure_location`) must be immediately visible to the other co-owner in their respective schedules.
- **`boat_uuid` is required.** All events created in this test must be tied to a valid `testBreezeId` to ensure the event is visible to the co-owners.

## Gotchas

- **Sole-owner normalization.** Per commit `ba1c3bd`, the system handles "sole-owner-Bob" normalization; this test relies on the fact that the creator of the event is treated as an authoritative participant to avoid unintended unauth-redirects or status regressions.
- **Data visibility latency.** The test assumes that `upsertSailingEvent` updates are synchronous and visible across different user sessions (Bob vs. Dan) immediately, which is a requirement for the `listMySchedule` view.

## Cross-cutting concerns

- **Auth**: Uses `bob` and `dan` identities to simulate two distinct co-owner sessions.
- **Side effects**: Changes to event logistics (departure/arrival) must propagate to both the `listMySchedule` view for the creator and the co-owner.

## External consumers

None known.

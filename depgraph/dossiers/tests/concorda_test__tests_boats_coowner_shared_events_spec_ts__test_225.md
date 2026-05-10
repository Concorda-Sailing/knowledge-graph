---
node_id: concorda-test::tests/boats/coowner-shared-events.spec.ts::test@225
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f886e99b20222e328e9ff8ef7dff3d291894641cfb25f4e1b4dce8f916e21cd9
status: current
---

# Dan modifies the event; the change is visible to Bob and Dan

## Purpose

Verifies that modifications made by one co-owner (e.g., Dan) to a shared sailing event are immediately visible to the other co-owner (e.g., Bob), and vice versa. This test ensures that the `upsertSailingEvent` logic correctly propagates changes to shared logistics like `departure_location` and `arrival_location` across different user schedules.

## Invariants

- **Shared state visibility**: Changes to a `sailing_event` via `upsertSailingEvent` must be reflected in the `listMySchedule` output for all users associated with that event.
- **Identity-based updates**: The test relies on two distinct `ApiClient` instances (`bob` and `dan`) to simulate independent users interacting with the same resource.
- **Dynamic data**: Uses `Date.now()` in string construction for `departure_location` and `arrival_location` to ensure uniqueness and avoid collision with static mock data.

## Gotchas

- **Traceability requirements**: Per commit `0990b5d`, tests in this file are expected to include `trace+screenshot artifacts` for debugging email-link flows; ensure any changes to the event-sharing logic maintain these artifacts.
- **Normalization dependency**: The test relies on the behavior of `sole-owner-Bob normalization` (from commit `ba1c3bd`) to ensure that even when one user is the primary owner, the co-owner's view remains consistent with the updated state.

## Cross-cutting concerns

- **Auth**: Uses two distinct authenticated `ApiClient` instances (`bob` and `dan`) to verify cross-user visibility.
- **Side effects**: Updates to the event via `upsertSailingEvent` affect the visibility of the event in both the `owner` and `coowner` schedule views.

## External consumers

None known.

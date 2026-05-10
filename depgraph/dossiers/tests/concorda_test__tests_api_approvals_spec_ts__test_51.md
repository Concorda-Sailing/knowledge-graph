---
node_id: concorda-test::tests/api/approvals.spec.ts::test@51
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ef87638fc0184d52e96ff9de43a03b24a600a1cfcd75bb7f955ab09dae129403
status: current
---

# lookup returns existing boat with owner list

## Purpose

Tests the lifecycle of a boat co-owner promotion request. It verifies that a user can request co-ownership, that the request is visible to the current owner via filtered lists, and that a single-owner vote correctly finalizes the status to `approved`. This test ensures the transition from `pending` to `approved` works correctly when the requester and voter are distinct identities.

## Invariants

- **Identity isolation**: Uses `aliceClient`, `bobClient`, and `carolClient` to simulate distinct users.
- **Request visibility**: A `pending` request must be visible to the requester via `requester=me` and to the voter via `voter=me`.
- **Status transition**: A `voteOnApprovalRequest` with the `approved` decision must result in a status of `approved`.
- **Subject filtering**: The `subject_uuid` filter in `listApprovalRequests` must return the finalized request after the vote.

## Gotchas

- **Cumulative state pollution**: A prior test run may leave a user as a co-owner, which causes subsequent `requestCoowner` calls to fail with a 400. Per commit `8644b3d`, the test must explicitly call `bob.removeCrewMember` to reset the state before attempting the flow.
- **Test skipping logic**: If the state reset (removing a crew member) fails, the test uses `test.skip(true, ...)` to avoid a false failure due to environmental-driven state leakage.

## Cross-cutting concerns

- **Auth**: Uses `aliceClient`, `bobClient`, and `carolClient` to establish identity.
- **Side effects**: Successful promotion changes the boat's owner/crew list, which affects the `lookupBoat` result.

## External consumers

None known.

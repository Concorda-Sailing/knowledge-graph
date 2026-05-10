---
node_id: concorda-test::tests/api/approvals.spec.ts::test@168
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9d9b9169fc79e1eeb6e3b5228322fc29cb11c8a2047742f533019369f9e758bf
status: current
---

# non-voter cannot vote on an unrelated request

## Purpose

Verifies that authorization logic correctly prevents users without ownership or voter status from interacting with approval requests. Specifically, it ensures that a user (Alice) who does not own a boat cannot submit a vote on a request created by another user (Carol) for that boat.

## Invariants

- **Requires a valid `request_id`** from a successful `requestCoowner` call to perform the vote attempt.
- **Expects a failure status code** (400, 403, or 404) when an unauthorized user attempts to POST to `/api/approval-requests/${request_id}/vote`.
- **Relies on `carolClient()` and `aliceClient()`** to establish distinct authenticated identities for the test.

## Gotchas

- **State-dependent failure:** The test includes a `test.skip` guard because `requestCoowner` might fail if the user is already a co-owner from a previous run. Per commit `8644b3d`, the suite attempts to reset co-owner state to ensure a clean flow, but if the reset fails or is bypassed, the test will skip rather than fail.

## Cross-cutting concerns

- **Auth**: Uses `carolClient` (owner/co-owner) and `aliceClient` (non-owner) to test permission boundaries.
- **Side effects**: The test performs a cleanup via `carol.cancelApprovalRequest(request_id)` to prevent orphaned approval requests in the test database.

## External consumers

None known.

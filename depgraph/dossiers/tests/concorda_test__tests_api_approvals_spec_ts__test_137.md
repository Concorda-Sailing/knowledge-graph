---
node_id: concorda-test::tests/api/approvals.spec.ts::test@137
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8b34851d6c4ceb9d952363c3f4cd4a1fe0b079f7f67a4cad95ba657844f2ee16
status: llm_drafted
---

# requester can cancel a pending request

## Purpose

Tests the capability of a requester (e.g., Carol) to cancel a pending co-owner request. This ensures that the lifecycle of an approval request can be terminated by the initiator before a decision is reached, preventing orphaned requests in the system.

## Invariants

- **Requires a valid `request_id`** generated from a prior `requestCoowner` call.
- **Returns a status of `'cancelled'`** upon successful cancellation.
- **The request must be in a pending state**; once a vote is cast or a decision is finalized, the cancellation flow changes.

## Gotchas

- **State-dependent failure:** If the user is already a co-owner (e.g., from a previous test run), the `requestCoowner` call will throw. The test uses a `try/catch` block to `test.skip` if this occurs, preventing a cascade of failures in the E2E suite.
- **Cleanup requirement:** As seen in the sibling test for non-voter access, manual cleanup via `cancelApprovalRequest` is often necessary to prevent state leakage between tests.

## Cross-cutting concerns

- **Auth**: Uses `carolClient()` to establish identity; requires the requester to have specific permissions on the `boatId`.
- **Side effects**: Successfully cancelling a request removes the pending item from the owner's notification/approval queue.

## External consumers

None known.

---
node_id: concorda-test::tests/boats/coowner-approval-vote.spec.ts::test@55
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9cf07487a877d7906ddf99717b2f65ab27c894e3c6453bea14112c67849113d0
status: llm_drafted
---

# owner can reject an incoming request with a reason

## Purpose

Verifies the "Reject" workflow for co-owner requests. It ensures that when an owner provides a reason and clicks reject, the request status transitions to `rejected` and the UI correctly removes the pending request from the visibility of the requester.

## Invariants

- **Requires two distinct identities**: An `aliceApi` (requester) and a `bobApi` (owner/approver) to simulate the two-party interaction.
- **Status transition**: The request must move from a pending state to a `rejected` status in the API response.
- **UI visibility**: The "Pending approvals" section must be hidden or empty after the rejection is processed.
- **Input requirement**: A reason string must be provided in the `Reason` placeholder field for the rejection to be valid.

## Gotchas

- **Idempotency/State collision**: If Alice is already a co-owner from a previous failed run, the `requestCoowner` call will throw. The test uses a `try/catch` block with `test.skip(true, ...)` to prevent failure due to existing state, as seen in the logic for `requestId`.
- **Race conditions on UI updates**: The test uses `expect.poll` for the status check and a `10_000`ms timeout for the visibility check to account for potential latency in the API/UI synchronization.

## Cross-cutting concerns

- **Auth**: Uses `ApiClient.login` for both the requester (Alice) and the owner (Bob).
- **Side effects**: A successful rejection changes the state of the `coowner-approval-vote` flow, affecting the visibility of the request in the `Pending approvals` panel.

## External consumers

None known.

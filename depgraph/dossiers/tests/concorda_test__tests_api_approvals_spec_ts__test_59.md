---
node_id: concorda-test::tests/api/approvals.spec.ts::test@59
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 408422e2897fd62bbdf965b048bc80c6577edd3d343fe36ce88701f8cc335dd1
status: llm_drafted
---

# lookup returns exists=false for unknown boat

## Purpose

Verifies the boat co-owner promotion workflow, specifically ensuring that a request initiated by a user can be voted on by an existing owner and result in a finalized state. It tests the transition from a `pending` request to an `approved` status via the `requestCoowner` and `voteOnApprovalRequest` API endpoints.

## Invariants

- **`request_id` is required.** The `requestCoowner` call must return a valid ID to proceed with the voting flow.
- **Status transitions are deterministic.** A successful vote with the `'approved'` decision must move the request status to `'approved'`.
- **`subject_uuid` is the primary lookup key.** Once a request is finalized, it must be retrievable via `listApprovalRequests` using the `subject_uuid`.
- **Voter identity is scoped.** The voter must be an existing owner (e.g., Bob) and the request must be visible on their `voter=me` list.

## Gotchas

- **Cumulative-state pollution requires manual cleanup.** Because the test environment is long-lived, a prior run might leave a user as a co-owner, causing `requestCoowner` to fail. Per commit `8644b3d`, the test must explicitly call `removeCrewMember` to reset the state before attempting the promotion flow.
- **Tests must use `test.skip` for state-related errors.** If the cleanup of a previous co-owner fails or if a user is already a co-owner, the test should skip rather than fail to avoid false negatives in the CI pipeline.

## Cross-cutting concerns

- **Auth**: Uses `aliceClient`, `bobClient`, and `carolClient` to simulate different permission levels (Requester vs. Voter).
- **Side effects**: Successful promotion changes the boat's crew/owner list, which affects the boat's ownership metadata.

## External consumers

None known.

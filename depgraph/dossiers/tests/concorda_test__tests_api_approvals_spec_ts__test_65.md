---
node_id: concorda-test::tests/api/approvals.spec.ts::test@65
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3460ccad328e4a69ed852dde2abc10a4b816e2867619ea0ad0f5c1347360552f
status: llm_drafted
---

# create → list → vote approve flow finalizes as approved

## Purpose

Verifies the end-to-end lifecycle of a boat co-owner approval request. It ensures that a user (the requester) can initiate a request for co-ownership, a second user (the voter/owner) can see and act upon that request, and that the resulting state (approved or rejected) correctly reflects the decision and the resolution reason.

## Invariants

- **Sequential state dependency**: The test relies on a specific sequence: `requestCoowner` -> `listApprovalRequests` (as requester) -> `listApprovalRequests` (as voter) -> `voteOnApprovalRequest`.
- **Majority rule requirement**: For the "approve" flow, the test assumes the voter is the sole owner so that the decision finalizes immediately upon voting.
- **Status transitions**: A successful approval must transition the request status to `'approved'` and include a non-null `voter_person_uuid` in the votes array.
- **Resolution reason requirement**: A rejected status must be accompanied by a `resolution_reason` that matches the provided string (e.g., "not yet" or "reject").

## Gotchas

- **Cumulative-state pollution**: Prior test runs can leave users in a co-owner state, which causes `requestCoowner` to fail. Per commit `8644b3d`, the test now includes a manual cleanup step using `bob.removeCrewMember` to ensure the boat is in a clean state before attempting to create a new request.
- **Strict error handling for setup**: If the setup/cleanup (e.g., `removeCrewMember` or `requestCoowner`) fails, the test uses `test.skip(true, ...)` to avoid false negatives caused by stale data in the test environment.

## Cross-cutting concerns

- **Auth**: Uses multiple `ApiClient` identities (`aliceClient`, `bobClient`, `carolClient`) to simulate different permission levels (Requester vs. Owner/Voter).
- **Side effects**: Successful completion of this flow updates the boat's crew/ownership records in the database.

## External consumers

None known.

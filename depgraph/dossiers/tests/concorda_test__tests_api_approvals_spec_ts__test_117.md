---
node_id: concorda-test::tests/api/approvals.spec.ts::test@117
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0d61c94c8626f3a1b157dca3d159d18853d0957bf281c2715cf16c31fd718580
status: llm_drafted
---

# vote reject path finalizes as rejected

## Purpose

Verifies the negative outcome path where a rejection decision is made on an approval request. It ensures that when a voter (Bob) submits a `rejected` decision, the request status transitions to `rejected` and the `resolution_reason` is populated correctly. This test is distinct from the "approve" path as it validates the finality of a rejection and the handling of the rejection metadata.

## Invariants

- **Status transition**: A `rejected` decision must result in a status of exactly `'rejected'`.
- **Reasoning requirement**: The `resolution_reason` must be present and match a regex of `not yet|reject` (case-insensitive).
- **Request ownership**: The test relies on a successful `requestCoowner` call to establish the `request_id` before the vote can be cast.

## Gotchas

- **Stateful dependency on `requestCoowner`**: If the user (Alice) is already a co-owner from a previous test run, the `requestCoowner` call will throw. The test uses a `try/catch` block with `test.skip(true, ...)` to handle this, as seen in the pattern used for `Carol` in the same file.
- **Order of operations**: The test requires a valid `boatId` from `getBobBoatId()` to ensure the request is contextually valid for the user attempting to vote.

## Cross-cutting concerns

- **Auth**: Uses `aliceClient()` and `bobClient()` to establish distinct identities; the rejection path specifically tests the interaction between the requester (Alice) and the voter (Bob).
- **Side effects**: A successful rejection/cancellation of a request affects the availability of the `subject_uuid` for future `listApprovalRequests` calls.

## External consumers

None known.

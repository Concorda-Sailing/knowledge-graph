---
node_id: concorda-test::tests/auth/email-link-flows.spec.ts::test@116
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bdd040a0f2f240f8472df8398b875b480a36bb7b27ef2adb8f787b0c3a466288
status: current
---

# decline link finalizes the request as rejected

## Purpose

Verifies that a user can decline an invitation via an emailed link and that the resulting state change is correctly reflected in the system. This test ensures that the "decline" action transitions the status of an approval request to `rejected` and that the UI correctly displays the rejection message to the recipient.

## Invariants

- **URL structure**: The decline URL must contain the pattern `/members/invite/decline/${requestId}`.
- **Identity switch**: The test must switch from the recipient's session (using `danToken`) to the requester's session (using `api.setToken`) to verify the status change.
- **Polling requirement**: The status change is not instantaneous; the test uses a poll to wait for the status to reach `rejected`.
- **UI feedback**: The recipient must see the text "Invite declined" after navigating to the decline URL.

## Gotchas

- **Cleanup requirement**: Per commit `b2f849a`, tests involving `BoatCrew` modifications must explicitly clean up (e.g., `api.removeCrewMember`) to ensure subsequent runs start with a clean state.
- **Race conditions in status polling**: The status check on the `listApprovalRequests` endpoint can be sensitive to timing; the `api.poll` helper is used to avoid flaky failures during the transition to `rejected`.

## Cross-cutting concerns

- **Auth**: Uses `api.setToken(danToken)` to simulate the recipient's session and `api.setToken(bobToken)` to verify the requester's view.
- **Side effects**: Verifies the status of `ApprovalRequest` objects via the `listApprovalRequests` endpoint.

## External consumers

None known.

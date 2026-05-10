---
node_id: POST::/api/approval-requests/{0}/vote
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cbea7768886f852da0416b8f97af57572086bc9029b5fd18a2188768b8ec4dac
status: llm_drafted
---

# POST /api/approval-requests/{request_id}/vote

## Purpose

Submits a decision (vote) on an existing approval request. It takes a `request_id` and a body containing the `decision` and an optional `reason`. This is distinct from the `/cancel` endpoint, which terminates a request without recording a formal vote/reason.

## Invariants

- **HTTP Method**: `POST`.
- **Authentication**: Requires a valid session via `require_auth`.
- **Input Shape**: Expects `ApprovalVoteCreate` containing `decision` and `reason`.
- **Return Type**: Returns the updated `ApprovalRequestRead` object via `_to_read`.

## Gotchas

- **IDOR Protection**: Per commit `c9a7c41`, this endpoint is subject to strict identity checks. The `voter_person_uuid` is derived directly from the authenticated `user.id` in the `approvals.cast_vote` call to prevent users from voting on behalf of others via ID manipulation.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the voter.
- **Audit**: Y (via `approvals.cast_vote` which records the decision and reason).
- **Side effects**: Updates the state of the specific `ApprovalRequest`, which may trigger UI updates in the request tracking dashboard.

## External consumers

- `concorda-web` (via `approvalsApi.vote`)
- `concorda-test` (via `ApiClient.voteOnApprovalRequest`)

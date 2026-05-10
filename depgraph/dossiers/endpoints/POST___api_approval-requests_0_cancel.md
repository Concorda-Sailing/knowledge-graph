---
node_id: POST::/api/approval-requests/{0}/cancel
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 52e86954f5d26c575ad20307ec554ee54f4e91baf490fdc639718e0d8373914f
status: llm_drafted
---

# POST /api/approval-requests/{request_id}/cancel

## Purpose

Provides a way to void an active approval request. It transitions an approval from an active state to a cancelled state by invoking `approvals.cancel_request`. This is distinct from `cast_vote`, which is used for making a decision (accept/reject) rather than terminating the request lifecycle entirely.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns the updated object** as an `ApprovalRequestRead` model.
- **Uses the `request_id` from the path** to identify the target resource.
- **The `acting_person_uuid` is derived from the authenticated user** to ensure the person cancelling the request is recorded in the audit trail.

## Gotchas

- **IDOR Vulnerability:** Per commit `c9a7c41`, this endpoint is subject to Tier-A IDOR (Insecure Direct Object Reference) audits. Ensure any changes to the logic do not bypass the ownership or permission checks required to cancel a specific request.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user).
- **Audit**: Y (via `approvals.cancel_request` which tracks the `acting_person_uuid`).
- **Side effects**: Cancelling a request may affect the visibility of pending actions on the dashboard/approval lists.

## External consumers

- `concorda-test::ApiClient.cancelApprovalRequest`
- `concorda-web::approvalsApi.cancel`

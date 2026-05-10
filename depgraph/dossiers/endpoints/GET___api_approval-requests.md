---
node_id: GET::/api/approval-requests
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1320b466de577aa751b5fe4461cf3a9d86004ba098797c71ff6075b4dd5d557d
status: current
---

# GET /api/approval-requests

## Purpose

Provides a mechanism for users to request and manage approvals for specific subjects (e.g., changes to events or organizations). It allows requesters to track their pending requests and allows voters to see requests relevant to them or to a specific subject. This endpoint is the primary interface for the approval lifecycle, including creating, voting on, and cancelling requests.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Strictly scoped by identity**: Users can only list requests where they are the `voter` (via `voter="me"`), the `requester` (via `requester="me"`), or a participant in a specific `subject_uuid`.
- **Returns a list of `ApprovalRequestRead` objects** when querying the list endpoint.
- **Admin bypass**: Users with `system_admin` or `org_admin` roles can bypass participant-based visibility constraints when querying by `subject_uuid`.

## Gotchas

- **IDOR Vulnerability**: Per commit `c9a7c41`, the `subject_uuid` query must strictly enforce participant-based visibility. If a user is not the requester or a voter, they cannot see the full history (including vote reasons and identities) unless they hold an admin role.
- **Mandatory Query Parameters**: The `list_` function will raise a `400` error if none of the three specific filters (`voter="me"`, `requester="me"`, or `subject_uuid`) are provided.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and checks for `system_admin` or `org_admin` roles for elevated visibility.
- **Audit**: Indirectly affects auditability of subject changes through the `reason` field in the `vote` method.

## External consumers

- `concorda-web`: Used by `approvalsApi.list` for rendering approval dashboards and request lists.
- `concorda-test`: Used by `ApiClient.listApprovalRequests` for end-to-end testing of approval flows.

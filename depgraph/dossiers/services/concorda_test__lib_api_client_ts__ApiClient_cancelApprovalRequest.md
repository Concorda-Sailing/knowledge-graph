---
node_id: concorda-test::lib/api-client.ts::ApiClient.cancelApprovalRequest
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fa63b032d0a55ee9fa044bed70295caab2a4246be889b993481eab7897798467
status: llm_drafted
---

# ApiClient.cancelApprovalRequest

## Purpose

The `cancelApprovalRequest` method provides a way to revoke a pending approval request via the API. It is used to transition an approval request out of a "pending" state when a user or system decides the request is no longer valid or necessary.

## Invariants

- **HTTP Method/Path** — Performs a `POST` to `/api/approval-requests/${requestId}/cancel`.
- **Return Shape** — Returns an `ApprovalRequest` object representing the updated state of the request.
- **Single Argument** — Requires a single `requestId` string to identify the target request.

## Gotchas

- **Auth/Policy mismatch** — Per commit `c70d472`, ensure the test setup handles pending policies correctly; if the user lacks the permission to cancel a specific request, the API may reject the call if the auth state isn't properly established in `globalSetup`.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token via `this.post`.
- **Side effects**: Used in `coowner-inbox.spec.ts` to manage stale pending invites, which affects the visibility of pending requests in the user's inbox.

## External consumers

None known.

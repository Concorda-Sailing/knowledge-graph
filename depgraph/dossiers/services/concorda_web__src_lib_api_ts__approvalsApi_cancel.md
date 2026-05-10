---
node_id: concorda-web::src/lib/api.ts::approvalsApi.cancel
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3bc2b3965a0e2ff0f04e1557cbb59ceb32a4f032d1c7d3df18dbe3eb66397918
status: llm_drafted
---

# approvalsApi.cancel

## Purpose

The `cancel` method provides a way to void a pending approval request. It is part of the `approvalsApi` service and is used when a user needs to retract a decision or stop a workflow that is currently in flight. Use this instead of `vote` when the intent is to invalidate the request entirely rather than submitting a specific decision.

## Invariants

- **Method is `POST`** — Requires a POST request to the specific resource endpoint.
- **Returns `ApprovalRequest`** — The response returns the updated state of the approval object.
- **Requires `id`** — The function expects a string representing the unique identifier of the approval request.
- **Uses `fetchApiAuthenticated`** — The call is protected by the standard authenticated fetch wrapper.

## Gotchas

- **Dependency on `OutgoingApprovalRow`** — This method is directly consumed by the `OutgoingApprovalRow` component in the inbox. Any change to the signature or return type will break the inbox UI for outgoing requests.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to cancel the specific request.
- **Side effects**: Canceling an approval may impact the visibility of the request in the `inbox/outgoing-row.tsx` component.

## External consumers

None known.

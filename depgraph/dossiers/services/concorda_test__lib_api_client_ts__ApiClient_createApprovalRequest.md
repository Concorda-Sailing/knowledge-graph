---
node_id: concorda-test::lib/api-client.ts::ApiClient.createApprovalRequest
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cf4161273b5008a3528643d501a6ff12bf39c5e5108f09b006fae6fb038649a1
status: llm_drafted
---

# ApiClient.createApprovalRequest

## Purpose

The `createApprovalRequest` method initiates a formal approval workflow for a specific subject (e.g., a policy or document). It is used to transition a subject into a state that requires human intervention or sign-off. Use this method when a test needs to simulate the creation of a pending action that a user must subsequently vote on via `voteOnApprovalRequest`.

## Invariants

- **HTTP Method: `POST`** — Always sends a POST request to the `/api/approval-requests` endpoint.
- **Payload Structure** — Requires a `request_type` (string), a `subject_uuid` (string), and an optional `target_state` (Record).
- **Returns `Promise<ApprovalRequest>`** — The response is the newly created approval request object, which includes the `id` needed for subsequent voting or cancellation.

## Gotchas

- **Endpoint mismatch in setup** — Per commit `c70d472`, ensure you are not attempting to use `/auth/accept-tos` logic for policy acceptance; `createApprovalRequest` is the correct way to initiate the workflow, but the actual acceptance of pending policies is handled by the distinct `acceptAllPendingPolicies` method.
- **Manual state transitions** — If a test fails to provide a valid `target_state` that the backend expects, the request may be created but will not trigger the expected downstream UI changes.

## Cross-cutting concerns

- **Auth**: Uses the `ApiClient` instance's bearer token. If `token` is not provided, it defaults to the instance's internal state.
- **Side effects**: Triggers the creation of a pending item in the user's approval queue, which may affect the visibility of "pending action" indicators in the UI.

## External consumers

None known.

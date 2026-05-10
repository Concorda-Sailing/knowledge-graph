---
node_id: concorda-test::lib/api-client.ts::ApiClient.voteOnApprovalRequest
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 97d69c071cb724b7ddc4ea3fd6dd3bcd7b2dc1015c25a082428bbc9774926931
status: llm_drafted
---

# ApiClient.voteOnApprovalRequest

## Purpose

Submits a decision (approval or rejection) to a specific approval request. This method is used to simulate user interactions with pending requests, such as a boat owner approving a crew member or a race organizer approving a sailing event. It is distinct from `cancelApprovalRequest`, which terminates the request without a decision.

## Invariants

- **HTTP Method is `POST`** — Sends the decision to the `/api/approval-requests/${requestId}/vote` endpoint.
- **Payload structure** — Requires a `decision` of either `'approved'` or `'rejected'`.
- **Returns `Promise<ApprovalRequest>`** — The response contains the updated state of the approval request.
- **Requires a valid `requestId`** — The operation is scoped to a specific resource ID.

## Gotchas

- **Decision-driven flows** — Recent work in `379ec4b` (cover emailed accept/decline links) indicates this method is a critical step in testing the "emailed accept/decline" flow for both co-owners and race-crew.
- **Implicit dependency on `requestId` existence** — If the `requestId` is invalid or the request has already been processed/cancelled, the API will return an error.

## Cross-cutting concerns

- **Auth**: Uses the `ApiClient`'s internal bearer token (set via `this.token`).
- **Side effects**: Successful votes trigger state changes in the approval lifecycle, which may impact the visibility of "pending" items in the UI for the requester.

## External consumers

None known.

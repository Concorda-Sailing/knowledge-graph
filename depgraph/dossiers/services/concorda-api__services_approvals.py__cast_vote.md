---
node_id: concorda-api::services/approvals.py::cast_vote
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bae30dd907bcf402caf7ea1b9a0aa1a6a47cde7acce47974e42bb3e955561c0a
status: llm_drafted
---

# cast_vote

## Purpose

Updates an existing `ApprovalVote` with a decision and an optional reason. This method transitions a vote from a `pending` state to a terminal state (`approved` or `rejected`). It is the primary mechanism for users to respond to requests, such as boat co-owner invites or membership requests.

## Invariants

- **Decision must be one of `("approved", "rejected")`** — any other value raises a 400 error.
- **Request status must be `pending`** — if the request is already finalized (e.g., via `cancel_request`), it raises a 409 error.
- **One vote per person per request** — if a vote already exists and is not `pending`, it raises a 409 error.
- **Returns the updated `ApprovalVote` object** — includes the new `decision`, `reason`, and `decided_at` timestamp.

## Gotchas

- **Membership enforcement occurs at the time of voting, not the time of invitation** — per commit `4c7de14`, the check for `_has_boat_management` is performed during the `cast_vote` call. This ensures that a user cannot bypass membership requirements by accepting an invite if their status changes between the invite being sent and the vote being cast.
- **Strict decision validation** — the function explicitly checks that the decision is either `"approved"` or `"rejected"`. This prevents accidental state corruption from invalid strings.
- **The `_evaluate` call is a side effect** — calling `cast_vote` triggers `_evaluate(db, req, latest_reason=reason)`, which may trigger downstream logic like finalizing the entire request if a majority/unanimous threshold is met.

## Cross-cutting concerns

- **Auth**: Requires a valid `voter_person_uuid` that is actually associated with the request.
- **Audit**: Updates the `decided_at` timestamp on the `ApprovalVote` record.
- **Side effects**: Triggers `_evaluate`, which can change the status of the parent `ApprovalRequest` and potentially trigger further lifecycle events (e.g., finalizing the request).

## External consumers

None known.

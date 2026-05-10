---
node_id: concorda-api::schemas/approval.py::ApprovalVoteCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7cbbcd132e10be31544baf85819a89ecbb6485e935773c5782c0d831ffec25a7
status: current
---

# ApprovalVoteCreate

## Purpose

Defines the schema for a user's vote on an approval request. It is used exclusively for the `POST /api/approval-requests/{id}/vote` endpoint to capture a decision and an optional justification. This is distinct from `ApprovalRequestCreate`, which defines the initial request structure; this schema is strictly for the subsequent voting action.

## Invariants

- **`decision` is a required string.** It must be exactly `"approved"` or `"rejected"`.
- **`reason` is optional.** It accepts an arbitrary string for providing context to the decision.
- **Input is a Pydantic model.** It is used to validate the request body of the vote endpoint.

## Gotchas

- **Strict decision values.** Per commit `1e5daf9` (feat: approvals), this schema was introduced as part of the new approval logic. The `decision` field is expected to be a specific string literal; passing values outside of the intended set (e.g., "pending") may cause validation errors depending on the router implementation.

## Cross-cutting concerns

- **Auth**: Requires authenticated user context (via the `POST /api/approval-requests/{id}/vote` router).
- **Audit**: Y (The decision and reason are typically logged as part of the approval history/audit trail).

## External consumers

- None known.

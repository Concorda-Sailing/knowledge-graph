---
node_id: concorda-api::models/approval_vote.py::ApprovalVote
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d371791e29680b4c9d9c90305cec1770f6139badce61b0de0fca760a1982aa7
status: llm_drafted
---

# ApprovalVote

## Purpose

The `ApprovalVote` model tracks individual decisions made by persons on specific approval requests. It is distinct from the `ApprovalRequest` model (which likely holds the aggregate state) by providing granular, per-user metadata like the specific `decision` and a text-based `reason`. Use this model when you need to audit who voted and why, rather than just the current status of the request.

## Invariants

- **Enforces uniqueness via `uq_approval_vote_request_voter`** — a single person can only submit one vote per request.
- **`request_uuid` and `voter_person_uuid` are required** — both must be valid 36-character UUID strings.
- **`decision` defaults to `"pending"`** — this is the initial state before a user-driven transition.
- **`decided_at` is nullable** — it should only be populated when the decision state changes from "pending".

## Gotchas

- **New model (commit `f39714a`)** — this model was introduced in the recent "feat(approvals)" commit. Any logic assuming a legacy approval system that didn't track individual voter reasons will need to be updated to account for this new granular data.

## Cross-cutting concerns

- **Auth**: Relies on `voter_person_uuid` to tie a vote to a specific authenticated identity.
- **Audit**: Provides the granular data (reason/decision) used for the audit trail of approval workflows.
- **Side effects**: Changes to this model (e.g., a new vote submitted) are the primary driver for updating the status of the parent `ApprovalRequest`.

## External consumers

- `GET /api/approval-requests` (via `routers/approvals.py`)

---
node_id: concorda-api::services/approvals.py::get_votes
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c760bd2af78831f03eb616c02d2df4170d3d0689feb1222401c610628447ee33
status: current
---

# get_votes

## Purpose

Retrieves all `ApprovalVote` records associated with a specific `request_id`. This is a low-level data retrieval helper used by the internal `_evaluate` function to determine if an `ApprovalRequest` has met its resolution criteria (e.g., unanimous, majority, or first-responder).

## Invariants

- **Input is a `request_id` (string)** which corresponds to the `request_uuid` in the `ApprovalVote` table.
- **Returns a list of `ApprovalVote` objects.** If no votes exist for the ID, it returns an empty list, not `None`.
- **Data is read-only.** This function performs a simple `SELECT` via SQLAlchemy and does not mutate the database state.

## Gotchas

- **Majority rule logic depends on the definition of "non-pending".** Per commit `2fe8ad5`, the majority calculation must only count cast votes (where `decision != "pending"`) to avoid division errors or incorrect thresholds.
- **The `request_id` must be the UUID of the request, not the subject.** While `list_requests_for_subject` filters by the subject, `get_votes` specifically filters by the `request_uuid` to ensure it only pulls votes for the specific lifecycle event.

## Cross-cutting concerns

- **Auth**: None (this is a pure data fetcher).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Indirectly affects the `_evaluate` and `_finalize` flow. If this returns unexpected data, it can trigger premature `on_approve` or `on_reject` hooks in the `ApprovalRequest` lifecycle.

## External consumers

None known. (Internal to `approvals.py` service logic).

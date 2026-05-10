---
node_id: concorda-api::services/approvals.py::list_requests_for_voter
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 623a7e685ca0d9e6c23f289eeaafa8bedbff3d9e7435090f07d4dcc7488497ae
status: llm_drafted
---

# list_requests_for_voter

## Purpose

Retrieves all `ApprovalRequest` objects associated with a specific voter via a join on `ApprovalVote`. This is the primary method for fetching a user's "pending actions" or "voting history" in the UI. Use this instead of `list_requests_for_requester` when the context is the person being asked to vote, rather than the person who initiated the request.

## Invariants

- **Joins on `ApprovalVote`** — The query requires a join between `ApprovalRequest` and `ApprovalVote` to filter by `voter_person_uuid`.
- **Returns `list[ApprovalRequest]`** — The output is a list of full request objects, not just IDs.
- **Optional `status` filter** — If `status` is provided, the result set is narrowed to requests matching that specific state (e.g., "pending").

## Gotchas

- **Double-finalize protection** — Per commit `2fe8ad5`, the logic in this module (specifically via `_evaluate` and `_finalize`) is designed to prevent multiple state transitions. Ensure that any logic calling this or related methods respects the fact that a request can only be finalized once.
- **Majority rule calculation** — Per commit `2fe8ad5`, the "majority" rule is sensitive to the distinction between total votes and cast votes. Ensure that any logic relying on the count of requests returned by this function accounts for the specific rule type (unanimous vs. majority) defined in the request spec.

## Cross-cutting concerns

- **Auth**: Relies on the caller to provide a valid `voter_uuid`.
- **Audit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.

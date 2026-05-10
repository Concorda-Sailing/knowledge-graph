---
node_id: concorda-api::services/approvals.py::list_requests_for_requester
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 510f96e010157241db6c2875cf0c1b46ff760eeb0e546e75169cb678aee414c0
status: llm_drafted
---

# list_requests_for_requester

## Purpose

Retrieves a list of `ApprovalRequest` objects where the specified `requester_uuid` is the initiator. This is distinct from `list_requests_for_voter`, which returns requests where the user is an active participant in the voting process. Use this when the UI needs to show a user "the things I have requested approval for."

## Invariants

- **Returns a list of `ApprovalRequest` objects.** The result is a standard Python list of SQLAlchemy model instances.
- **`status` filter is optional.** If `status` is provided, the query is narrowed to specific lifecycle stages (e.g., "pending", "approved", "rejected").
- **Filtering is performed on `requester_person_uuid`.** This field is the primary key for the relationship between the requester and the request.

## Gotchas

- **Double-finalize protection.** Per commit `2fe8ad5`, ensure that any logic calling this or related functions respects the existing status to avoid redundant state transitions or side effects during the evaluation phase.

## Cross-cutting concerns

- **Auth**: Relies on the caller to ensure the `requester_uuid` is authorized to view these specific requests (typically handled at the API route level).
- **Side effects**: Indirectly affects the lifecycle of an approval; if this is used to drive a UI that triggers `_evaluate`, it may lead to status changes in the `ApprovalRequest` table.

## External consumers

None known.

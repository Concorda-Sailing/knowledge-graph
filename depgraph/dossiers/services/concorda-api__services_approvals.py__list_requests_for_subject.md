---
node_id: concorda-api::services/approvals.py::list_requests_for_subject
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fa03e4a08eba05212e95dc7b81def54201b7a289df231a114d81dd1e99ab48ea
status: current
---

# list_requests_for_subject

## Purpose

Retrieves all `ApprovalRequest` records associated with a specific subject (e.g., a boat or a person). This is a read-only query used to aggregate pending or completed requests for a given entity. It is distinct from `list_requests_for_requester`, which filters by the person initiating the request rather than the entity being acted upon.

## Invariants

- **Returns a list of `ApprovalRequest` objects.** The result is a standard list of SQLAlchemy model instances.
- **No filtering logic.** Unlike `list_requests_for_requester`, this function does not accept a `status` argument; it returns all requests for the subject regardless of their current state (pending, approved, or rejected).
- **Database session required.** Requires an active `db: Session` to execute the query.

## Gotchas

- **Subject identity is critical.** Because this is a raw query, ensure the `subject_uuid` passed is the correct entity type (e.g., a Boat UUID vs. a Person UUID) to avoid returning unrelated or empty results.

## Cross-cutting concerns

- **Auth**: None (this is a raw DB fetch; higher-level API routes calling this must handle permission checks).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.

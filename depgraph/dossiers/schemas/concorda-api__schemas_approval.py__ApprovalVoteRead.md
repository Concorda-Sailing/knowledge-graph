---
node_id: concorda-api::schemas/approval.py::ApprovalVoteRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fcacee0b290bda8a889929cc2d24580e40484c88230bdbaaf59151c01702a2ad
status: llm_drafted
---

# ApprovalVoteRead

## Purpose

The read-only representation of a single vote cast on an approval request. It provides the decision outcome, the voter's identity, and the timestamp of the decision. This is a sub-component of the `ApprovalRequestRead` model, used to populate the `votes` list.

## Invariants

- **`id` is a string-based UUID.**
- **`decision` is a required string.** It represents the outcome of the vote.
- **`voter_person_uuid` is a required string.** This links the vote to a specific person in the system.
- **`decided_at` is an optional datetime.** It tracks when the decision was finalized.
- **`from_attributes = True` is required.** This allows the Pydantic model to be instantiated directly from ORM objects (e.g., SQLAlchemy models).

## Gotchas

- **`decision` is a raw string.** Per `ApprovalVoteCreate`, this is expected to be `"approved"` or `"rejected"`. Downstream consumers (like the web UI) must handle these specific string values rather than relying on an Enum, as the current schema uses a raw `str`.

## Cross-cutting concerns

- **Auth**: None (this is a read-only schema; authorization is handled at the endpoint level).
- **Websocket**: None.
- **Audit**: N/A (the vote itself is the audit record for an approval request).
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.

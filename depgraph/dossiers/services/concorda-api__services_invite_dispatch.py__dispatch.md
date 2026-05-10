---
node_id: concorda-api::services/invite_dispatch.py::dispatch
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 668e6a17624c91b1a3556b8b2601a3c0aeb1aa07b9e39c4fd37891c23f0df185
status: llm_drafted
---

# dispatch

## Purpose

The central dispatcher for processing incoming invitation responses (accept/decline). It abstracts the differences between various domain-specific invitation types (e.g., `ApprovalRequest` vs. `EventCrew`) by routing a generic `invite_id` to a registered handler that understands the specific database schema and internal vocabulary. Use this when adding a new type of invitation-based interaction that requires a user to "respond" to a request.

## Invariants

- **`decision` must be exactly `"accepted"` or `"declined"`** to maintain the wire format contract across all handlers.
- **Returns an `InviteResponse` object** containing the handler's `kind` and a status (e.g., `"recorded"`, `"already"`, or `"error"`).
- **The `dispatch` function is a linear search** through the `_HANDLERS` list; the first handler to successfully `find` the `invite_id` owns the execution.
- **Throws `HTTPException(400)`** if the decision string is not one of the two allowed values.
- **Throws `HTTPException(404)`** if no registered handler can locate the provided `invite_id`.

## Gotchas

- **Vocabulary Mapping:** Handlers must map the generic `"accepted"`/`"declined"` inputs to their specific internal enums. For example, `_ApprovalRequestHandler` maps `"accepted"` to `"approved"` and `"declined"` to `"rejected"`.
- **Idempotency/Error Handling:** Per the `_ApprovalRequestHandler` logic, a `409 Conflict` from the underlying service (like `approvals.cast_vote`) should be caught and returned as a status of `"already"` rather than bubbling up as a hard error to the client.
- **Status-based Routing:** As noted in `_EventCrewHandler`, the same table can represent both an invitation (owner $\to$ sailor) and a request (sailor $\to$ owner); the handler must use the row's status to determine the correct authorization path.

## Cross-cutting concerns

- **Auth**: Relies on the `user_id` passed from the router to validate the voter/responder.
- **Side effects**: Triggers state changes in `ApprovalRequest` and `EventCrew` tables, which may impact visibility of invitation status in the UI.

## External consumers

- `POST /api/invite/respond` (via `routers/invite_response.py`)

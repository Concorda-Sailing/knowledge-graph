---
node_id: concorda-api::services/invite_dispatch.py::register_handler
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e666b9e30d7a51b99b2a3e67fe5531f58c059b1ffb2ad6d9fb841edc8b5cd43
status: current
---

# register_handler

## Purpose

Registers a new `InviteHandler` into the global `_HANDLERS` list. This function is the entry point for the plugin-style dispatch pattern used to process incoming decisions (like accepting or declining an invite) for different types of entities (e.g., `ApprovalRequest` or `EventCrew`). It allows the system to decouple the high-level "decision" event from the specific domain logic and internal vocabulary of the target entity.

## Invariants

- **Idempotency**: Calling `register_handler` with the same handler instance does not create duplicate entries in the `_HANDLERS` list.
- **Order-dependent lookup**: Handlers are processed in the order they are registered; the first handler that successfully `find`s the `invite_id` owns the execution.
- **Input restriction**: The `decision` string must be exactly `"accepted"` or `"declined"` to maintain the wire format contract across the dispatch chain.

## Gotchas

- **Vocabulary Mapping**: Handlers must map the generic `"accepted"/"declined"` inputs to their specific internal enums (e.g., `_ApprovalRequestHandler` maps to `"approved"/"rejected"`). Failure to do this correctly breaks the unified dispatcher pattern established in commit `605c924`.
- **Exception Handling**: The `_ApprovalRequestHandler` specifically catches `409` errors from `approvals.cast_vote` to return a status of `"already"`. This ensures that if a user attempts to re-submit a decision, the UI receives a graceful state rather than a hard error.

## Cross-cutting concerns

- **Auth**: Handlers must validate that the `user_id` provided is the legitimate target/voter for the specific `invite_id` (per docstring in `register_handler`).
- **Side effects**: Triggers state changes in `approvals.py` (e.g., `cast_vote`) and potentially updates `EventCrewStatus` via the `dd72f2f` pattern.

## External consumers

None known.

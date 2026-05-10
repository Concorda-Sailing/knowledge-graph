---
node_id: concorda-api::services/approvals.py::create_request
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b2ed9cecdb615c62be4839c0ac05a26fc5dfec94d4327635467dc8a28a422485
status: current
---

# create_request

## Purpose

Initializes and dispatches an `ApprovalRequest` based on a specific `request_type`. It resolves the request's configuration (voters, validation logic, and expiry) via a type-specific spec, creates the initial `pending` record, and handles the immediate creation of `ApprovalVote` entries for all required voters. If no voters are required, it automatically triggers the `_finalize` process to move the request to an approved state.

## Invariants

- **`status` is initialized to `"pending"`** — the lifecycle must start in this state before any `cast_vote` calls can occur.
- **`target_state` defaults to `{}`** — if not provided, an empty dictionary is used to prevent attribute errors in downstream logic.
- **`voter_ids` are de-duplicated** — the function uses a `seen` set to ensure a single person cannot be assigned multiple pending votes for the same request.
- **`spec["validate"]` is called before commit** — the validation logic is part of the creation transaction to ensure the request is valid before it is persisted.

## Gotchas

- **Membership enforcement is on the accept, not the send** — per commit `4c7de14`, the requirement for "Boat Owner" membership is enforced during `cast_vote` (specifically for `boat_coowner_invite`), not during the initial `create_request` call.
- **Automatic approval for zero-voter requests** — if `spec["voters"]` returns an empty list, the function calls `_finalize(db, req, "approved")` immediately. This bypasses the standard voting lifecycle.
- **Double-finalize protection** — per commit `2fe8ad5`, the system must guard against multiple finalizations; while `create_request` handles the "zero-voter" edge case, subsequent state transitions rely on the `status` check in `cast_vote`.

## Cross-cutting concerns

- **Auth**: Relies on `requester_person_uuid` to identify the initiator; downstream `cast_vote` requires the voter to be a valid participant.
- **Websocket**: Triggers `_dispatch_notifications` with the `"created"` event type.
- **Audit**: Creates `ApprovalVote` rows in the database to track the intent of the request.
- **Side effects**: Triggers the `on_create` hook in the request spec, which may impact related entity states (e.g., updating boat ownership or membership status).

## External consumers

None known.

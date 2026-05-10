---
node_id: concorda-api::services/approvals.py::cancel_request
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5073a4201ae029b48e10602838ef8e348e44601e740b3256b2d36d2be03f1e06
status: llm_drafted
---

# cancel_request

## Purpose

Provides the logic to terminate a pending approval request by transitioning its state to "canceled". This is a distinct action from voting, as it allows the requester to retract a request before a decision is reached. It is used to prevent stale or unwanted requests from remaining in the system.

## Invariants

- **Status must be "pending"** — If the request is already in a terminal state (e.g., "approved" or "rejected"), the function raises a 409 error.
- **Identity check** — The `acting_person_uuid` must match the `requester_person_uuid` of the request, otherwise a 403 error is raised.
- **Uses `_finalize`** — The transition to "canceled" is handled via the internal `_finalize` helper to ensure consistent state transitions.
- **Returns the `ApprovalRequest` object** — The method returns the updated object after the database commit.

## Gotchas

- **Double-finalize protection** — Per commit `2fe8ad5`, the system must guard against multiple finalization attempts. `cancel_request` relies on the `req.status != "pending"` check to prevent accidental re-processing of already closed requests.
- **Strict ownership** — Only the original requester can trigger this. If a voter attempts to call this via an API endpoint, the `acting_person_uuid` check will trigger a 403.

## Cross-cutting concerns

- **Auth**: Requires `acting_person_uuid` to match the request requester.
- **Audit**: N/A.
- **Side effects**: Transitions the request to a terminal state, which may affect downstream logic that monitors for "pending" requests.

## External consumers

None known.

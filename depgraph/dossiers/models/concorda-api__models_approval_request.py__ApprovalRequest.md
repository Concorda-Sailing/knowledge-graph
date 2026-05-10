---
node_id: concorda-api::models/approval_request.py::ApprovalRequest
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8f14a1e5ce64e064c63d536da1e7a7eb981311fb40b1fe2a5e816098003ee884
status: llm_drafted
---

# ApprovalRequest

## Purpose

The core data model for tracking asynchronous approval workflows. It captures the intent of a requester (via `subject_type` and `subject_uuid`) and the state of the pending decision. This model is distinct from a simple boolean flag because it stores the `target_state` (the snapshot of data to be applied upon approval) and the `resolution_reason`.

## Invariants

- **`request_type` is required** and must be a non-null string.
- **`subject_uuid` must be a valid 36-character UUID string** to ensure compatibility with the `subject_type` it references.
- **`status` defaults to `"pending"`** and is used to drive the lifecycle of the request.
- **`target_state` is a JSON-compatible dictionary** representing the state change to be applied once the request is resolved.

## Gotchas

- **`subject_uuid` is a string, not a UUID type.** While it represents a UUID, the database stores it as a `String(36)` to avoid strict type-checking issues during polymorphic lookups.
- **Newer models like this one are part of the `feat(approvals)` expansion** (commit `f39714a`). Ensure any logic involving `ApprovalRequest` accounts for the fact that `target_state` and `resolution_reason` are nullable.

## Cross-cutting concerns

- **Auth**: Controlled via the `POST /api/approval-requests/{0}/vote` and `/cancel` endpoints.
- **Audit**: The `resolution_reason` and `resolved_at` fields serve as the primary audit trail for why a state change occurred.
- **Side effects**: Successful resolution of an `ApprovalRequest` typically triggers a state update on the subject entity (e.g., updating a boat's status or a user's permission level).

## External consumers

None known.

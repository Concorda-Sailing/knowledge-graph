---
node_id: concorda-web::src/lib/api.ts::approvalsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f3e532e146962ec852bc11e27e21a07dafa89fba96cfe70d3ba8cb74d1013c57
status: current
---

# approvalsApi.create

## Purpose

Initiates a new approval request within the system. This method is used to trigger a formal request for review or decision-making on a specific subject (e.g., a boat, a crew member, or a schedule change). It is distinct from `vote` or `cancel`, which act upon existing requests; `create` is the entry point for the lifecycle of an approval.

## Invariants

- **POST to `/api/approval-requests`** — This is the only endpoint for creating new requests.
- **Requires a `subject_uuid`** — The request must be tied to a specific entity in the system.
- **Returns an `ApprovalRequest` object** — The response contains the full state of the newly created request.
- **Uses `fetchApiAuthenticated`** — The caller must be authenticated to initiate a request.

## Gotchas

- **`target_state` is an optional record** — While the type is `Record<string, unknown>`, the API expects this to represent the state the subject should transition to upon approval.
- **Implicit dependency on `subject_uuid` existence** — If the subject (e.g., a boat or event) is deleted or invalid, the creation will fail at the API level.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Creating a request typically triggers downstream visibility in the dashboard or specific detail pages (e.g., the "incoming co-owner invites" pattern seen in `e02996c`).

## External consumers

None known.

## Open questions

- Should the `request_type` be an enum rather than a raw `string` to prevent malformed request types from reaching the backend?

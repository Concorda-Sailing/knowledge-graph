---
node_id: concorda-api::schemas/approval.py::ApprovalRequestCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3e9823a12a6c2272bbec9c9f6e020ab9d66ea3a9f2287a0ba2d057583f728593
status: current
---

# ApprovalRequestCreate

## Purpose

The Pydantic schema for initiating an approval request. It defines the payload required to trigger a new approval workflow, specifically identifying the type of request and the subject being acted upon. Use this when creating a new entry via the `POST /api/approval-requests` endpoint.

## Invariants

- **`request_type` is a required string.** It must be provided to distinguish between different approval workflows.
- **`subject_uuid` is a required string.** This identifies the specific entity (e.g., a boat or event) that the approval pertains to.
- **`target_state` is an optional dictionary.** It allows for passing arbitrary state data required for specific approval logic.

## Gotchas

- **Rich labels are server-side only.** Per commit `33d2dec`, fields like `boat_name` or `requester_name` are part of the broader context/response-side logic; this `Create` schema focuses strictly on the input identifiers (`subject_uuid`) to ensure the client doesn't try to "force" names that the server must resolve.

## Cross-cutting concerns

- **Auth**: Handled by the `POST /api/approval-requests` router.
- **Side effects**: Triggers the "rich emails and approval response labels" logic (per commit `33d2dec`) which affects how co-owner invites and approval notifications are rendered to users.

## External consumers

- `POST /api/approval-requests` (via `routers/approvals.py`)

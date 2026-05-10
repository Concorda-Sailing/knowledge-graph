---
node_id: POST::/api/approval-requests
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1b40aba50bba26212376d9e21de8318abcb302c5d0754d65f9a51be6fbf00ff2
status: current
---

# POST /api/approval-requests

## Purpose

Manages the lifecycle of approval requests, including creation, voting, and cancellation. It provides a mechanism for users to request permission or changes (e.g., for sailing events or organizational changes) and for designated voters to respond with a decision and an optional reason.

## Invariants

- **POST `/`** requires an `ApprovalRequestCreate` body and returns an `ApprovalRequestRead` model.
- **POST `/{request_id}/vote`** uses the authenticated `user.id` as the `voter_person_uuid` to prevent identity spoofing.
- **GET `/`** requires specific query parameters (`voter=me`, `requester=me`, or `subject_uuid`) to prevent unauthorized enumeration.
- **`subject_uuid` scoping** ensures that non-admin users can only see approval history for subjects they are directly involved with (as a requester or a voter).

## Gotchas

- **IDOR Vulnerability in `list_`**: Per commit `c9a7c41`, the `subject_uuid` filter must strictly enforce participant-only visibility. Without the manual check for `is_voter` (lines 86-91), any authenticated user could enumerate and read the full history (including private vote reasons) of any subject by guessing UUIDs.
- **Admin Bypass**: Only users with `system_admin` or `org_admin` roles can bypass the participant-only restriction when querying by `subject_uuid`.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (via `AuthUser`).
- **Audit**: Writes to the database via `approvals.create_request` and `approvals.cast_vote`.
- **Side effects**: Changes to the state of an approval (e.g., via `vote` or `cancel`) may affect the visibility of the subject's status in the UI.

## External consumers

- `concorda-web` (via `approvalsApi.create`)
- `concorda-test` (via `ApiClient.createApprovalRequest`)

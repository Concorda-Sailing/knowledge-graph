---
node_id: POST::/api/boats/{0}/coowner-invite
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 54a9d78746c2a81c8afb6d031424cb0e2267a40f188f78e4db11a9cd3c87f2af
status: current
---

# POST /api/boats/{boat_id}/coowner-invite

## Purpose

Allows a boat owner to invite another person to become a co-owner of a specific boat. The endpoint resolves the identity via either a `person_uuid` (preferred for directory selection) or an `email` (fallback for manual entry). It stages the user as a "crew" member with an "invited" status to prevent unauthorized roster access before the invite is accepted.

## Invariants

- **Requires `boat_id` and a body containing either `person_uuid` or `email`.**
- **Auth is mandatory.** Must be called by a user with owner permissions for the specific `boat_id` via `_require_owner`.
- **Returns a `request_id`.** The response shape is `{"request_id": <uuid>}`.
- **Status is staged as `invited`.** The user is added to `BoatCrew` with `role="crew"` and `status="invited"` to ensure they do not gain active permissions until the approval flow is completed.

## Gotchas

- **Eligibility is deferred.** Per commit `4c7de14`, the system does not check if the invitee is a "Boat Owner" at the time of the invite; the check is performed when the invite is accepted. This prevents blocking the invite process but requires the user to handle the upgrade prompt later.
- **Identity resolution failure.** If an `email` is provided that does not exist in the system, the API returns a 404. This is a deliberate design to prevent "ghost" invites that can never be accepted.
- **Prevents duplicate ownership.** If the target is already an "owner" of the boat, the API returns a 400 error to prevent redundant permission escalation.

## Cross-cutting concerns

- **Auth**: Enforced via `require_auth` and the `_require_owner` guard.
- **Audit**: Triggers the `create_request` service to generate a `boat_coowner_invite` type request in the approvals system.
- **Side effects**: Successful invites create a `BoatCrew` entry with `status="invited"`, which affects the visibility of the person in the boat's roster/crew list.

## External consumers

- `concorda-web` (via `boatApi.coownerInvite`)
- `concorda-test` (via `ApiClient.coownerInvite`)

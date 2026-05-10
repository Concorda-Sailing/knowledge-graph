---
node_id: concorda-web::src/lib/api.ts::boatApi.coownerInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aadfbedefceae431b24d435790eac951cf90b7f31dd3427618daeb2e4f31ec1a
status: current
---

# boatApi.coownerInvite

## Purpose

Sends a POST request to invite a specific person to become a co-owner of a boat. It accepts either a `person_uuid` or an `email` address as the payload. This is the primary method for expanding boat ownership via the web UI, distinct from `requestCoowner` which is used for requesting access rather than direct invitation.

## Invariants

- **Method/Path**: `POST /api/boats/${boatId}/coowner-invite`.
- **Payload**: The `invitee` object must contain either `person_uuid` or `email`.
- **Return Shape**: Returns an object containing a `request_id: string`.
- **Authentication**: Requires a valid bearer token via `fetchApiAuthenticated`.

## Gotchas

- **Membership Requirement**: Per commit `47688ac`, the API requires the inviter to have "Boat Owner" membership to successfully execute this request.
- **UX Flow**: Per commit `eb382d2`, this is used in conjunction with a "directory-only invite dialog" which may include an upgrade-prompt fallback if the user lacks sufficient permissions.
- **Identity Resolution**: The function supports both `person_uuid` and `email`, but the backend behavior for email-based invites is tied to the "directory-first" UX pattern described in commit `9e1cc53`.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has the necessary permissions to modify boat ownership.
- **Side effects**: Invites generated here drive the "incoming co-owner invites" display in the dashboard (per commit `e02996c`).

## External consumers

- `InviteCoownerDialog` in `owners-section.tsx`.

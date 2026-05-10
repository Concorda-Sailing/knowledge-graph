---
node_id: GET::/api/boats/{0}/pending-invites
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 195370a56e54d6793188b720238a8fcc711a1ec82f1083d3f426c50401239c75
status: llm_drafted
---

# GET /api/boats/{boat_id}/pending-invites

## Purpose

Retrieves a list of pending crew invites for a specific boat. This is used to display "unclaimed" or "pending" invites (typically via email-based links) in the boat's crew management interface. It is distinct from the `create_share_invite` flow, which generates single-use tokens for QR codes/links; this endpoint specifically surfaces the email-based `PendingCrewInvite` records.

## Invariants

- **Method is `GET`** and requires a valid `boat_id`.
- **Returns a list of `PendingInviteRead` objects**, containing `email`, `role`, `invited_by_uuid`, and timestamps.
- **Requires `require_auth`** via the `current_user` dependency.
- **Membership check is mandatory**: The caller must have an `active` or `invited` status in the boat's membership list to view these invites.

## Gotchas

- **Strict authorization required**: Per commit `36ef425`, the endpoint requires the user to have an `active` or `invited` status. If a user is merely a "crew" member but their status is not one of these two, they will receive a 403.
- **Visibility is tied to membership**: A user cannot see pending invites for a boat unless they are already part of the crew (or an invited member). This prevents unauthorized users from scraping potential crew email addresses.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and validates that the `current_user` has a valid membership status (`active` or `invited`) for the requested `boat_id`.
- **Side effects**: Data returned here is used to populate the "Invited" section of the boat crew table in the web UI.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.getPendingInvites`

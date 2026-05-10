---
node_id: POST::/api/boats/{0}/crew/invite-batch
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 675f3d438c4fb96ac14ccad00e982f0704819d45e6c95efbd082989e40c26d8d
status: current
---

# POST /api/boats/{boat_id}/crew/invite-batch

## Purpose

Allows a boat owner to invite multiple people to join a boat's crew via email addresses in a single request. It handles both existing users (adding them to `BoatCrew`) and non-members (creating a `PendingCrewInvite` with a secure token). This is the primary mechanism for scaling crew recruitment without requiring manual one-by-one invites.

## Invariants

- **Max 20 emails per request.** The implementation explicitly slices the input list to the first 20 unique, non-empty strings.
- **Requires Boat Ownership.** The `_require_owner` guard ensures only the boat's owner can trigger this endpoint.
- **Returns `BatchInviteResult`.** The response shape is strictly `{invited: int, skipped: int, errors: list[str]}`.
- **Email normalization.** All input emails are stripped and converted to lowercase to prevent duplicate invites due to casing.
- **Token security.** For new users, a `raw_token` is generated via `secrets.token_urlsafe(32)` and stored as a SHA-256 hash in the database.

## Gotchas

- **Ownership requirement.** Per commit `4c7de14`, the endpoint enforces that the `current_user` must be the Boat Owner, not just a member with a high role.
- **Pending invite expiry.** Per commit `8971b1c`, pending invites have a specific TTL (defined by `PENDING_INVITE_TTL_DAYS`). If an invite is not accepted within this window, the `PendingCrewInvite` becomes invalid.
- **Duplicate prevention.** If a user is already a member of the boat, they are skipped rather than re-invited, preventing redundant `BoatCrew` entries.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes the `_require_owner` check.
- **Audit**: N/A.
- **Side effects**: Triggers the creation of `PendingCrewInvite` records which are consumed by the email-based acceptance flow (see commit `8c29970`).

## External consumers

- `concorda-web`: Used by `boatApi.inviteCrewBatch` for the crew management interface.
- `concorda-test`: Used by `ApiClient.inviteCrewByEmail` for end-to-end testing of recruitment flows.

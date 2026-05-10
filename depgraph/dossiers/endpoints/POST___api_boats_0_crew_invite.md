---
node_id: POST::/api/boats/{0}/crew/invite
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 657eda98c380a6fbc5c20aaaa59896aff62eeefd3c165ef76ce1d0ae9855ac95
status: current
---

# POST /api/boats/{boat_id}/crew/invite

## Purpose

The endpoint allows a boat owner to invite a specific person to join their boat's crew. It generates a secure, one-time `invite_token` (SHA-256 hashed version stored in DB) and triggers an email invitation. This is distinct from general "crew requests" as it is an outbound action initiated by the owner to a specific `person_uuid`.

## Invariants

- **Method/Path**: `POST /{boat_id}/crew/invite`.
- **Auth**: Requires `require_auth` and specifically calls `_require_owner(db, boat_id, current_user.id)`.
- **Return Shape**: Returns a `BoatCrewRead` object on success (201 Created).
- **Uniqueness**: Fails with `409 Conflict` if the `person_uuid` is already a member of the boat's crew.
- **Token Generation**: Uses `secrets.token_urlsafe(32)` for the raw token and stores the `sha256` hash in the database.

## Gotchas

- **Ownership Enforcement**: Per commit `4c7de14`, the system now enforces that the inviter must be a Boat Owner at the time of the invite, not just a member.
- **Email Failure Resilience**: The `send_boat_crew_invitation_email` call is wrapped in a broad `except Exception: pass` block. If the email service fails, the database transaction still commits and the crew record is created, but the user will not receive the invitation.
- **Identity Context**: The `inviter_name` is constructed by looking up the `current_user.id` in the `Person` table. If the user exists in the auth system but lacks a corresponding `Person` record, the email defaults to "A boat owner".

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and `_require_owner`.
- **Websocket**: Emits `BOAT_CREW_UPDATED` event for the given `boat_id` upon successful commit.
- **Side effects**: Triggers an email via `send_boat_crew_invitation_email`.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.inviteCrew` (via `api.ts:3123`).

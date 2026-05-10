---
node_id: POST::/api/boats/{0}/crew/{1}/resend-invite
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65804b19a8e0b9e732c197176da14038b23ba12f654a2949458ac6fb92c39c7d
status: current
---

# POST /api/boats/{boat_id}/crew/{crew_id}/resend-invite

## Purpose

Resends a pending crew invitation by generating a new unique token and resetting the timestamp. This endpoint handles two distinct scenarios: updating an existing `BoatCrew` record (where the status must be `"invited"`) or updating a `PendingCrewInvite` record. It is used to ensure that if an original invite link has expired or been lost, the boat owner can trigger a fresh, valid email to the recipient.

## Invariants

- **Requires `_require_owner`** — The `current_user` must be the owner of the boat to execute this; it is not a general crew-level permission.
- **POST method** — Always uses `POST` to ensure the side-effect of token generation and email dispatch is idempotent-safe in the eyes of the client.
- **Returns `{"message": "Invite resent"}`** — A successful operation returns this specific JSON shape.
- **Generates a new `raw_token`** — A new 32-byte `secrets.token_urlsafe` string is generated and hashed via SHA-256 before being stored in the database.
- **Updates `created` or `modified`** — Depending on the record type, the timestamp is reset to `datetime.utcnow()` to refresh the lifecycle.

## Gotchas

- **Status check is strict** — If calling on a `BoatCrew` record, the status must be exactly `"invited"`. If the status is anything else (e.g., `"accepted"`), it raises a `400 BAD REQUEST`.
- **Silent email failures** — The `try/except` block around `send_boat_crew_invitation_email` suppresses exceptions. If the email service fails, the database transaction still commits and the token is updated, but the user receives no notification.
- **`PENDING_INVITE_TTL_DAYS` dependency** — For `PendingCrewInvite` records, the `expires_at` field is set using this constant. Changing this constant affects the lifecycle of resents.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and specifically enforces `_require_owner` for the `boat_id`.
- **Websocket**: Emits `BOAT_CREW_UPDATED` for the `boat_id` upon successful commit.
- **Audit**: N/A.
- **Rate limit**: None explicitly defined in this endpoint.
- **Side effects**: Triggers a refresh of the crew list/status in the UI via the `BOAT_CREW_UPDATED` broadcast.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.resendInvite`

---
node_id: DELETE::/api/boats/{0}/crew/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 67b6dc6f4dbf77cd99bbacf01e271a0412912f1242baa433e6275597a2712816
status: current
---

# DELETE /api/boats/{boat_id}/crew/{crew_id}

## Purpose

Removes a crew member from a boat or cancels a pending crew invite. This endpoint is the primary mechanism for managing boat membership, handling both active `BoatCrew` records and `PendingCrewInvite` records. It is distinct from the `resend-invite` endpoint, which only resets the token/timestamp for an existing invite.

## Invariants

- **Method is `DELETE`**.
- **Requires `require_auth`** — the caller must be authenticated.
- **Enforces `_require_owner`** — only the boat owner can execute this deletion.
- **Returns `{"message": "..."}`** on success, with the specific reason (removal vs. cancellation) implied by the internal logic.
- **Returns `404 Not Found`** if neither a `BoatCrew` record nor a `PendingCrewInvite` record matches the provided `boat_id` and `crew_id`.

## Gotchas

- **Self-removal protection** — per the logic in `remove_crew`, if the `crew.role` is "owner" and the `person_uuid` matches the `current_user.id`, the API raises a `400 Bad Request`. You cannot remove yourself as the sole owner via this endpoint.
- **Ownership requirement** — `_require_owner` is a hard dependency. If the user is a co-owner but not the primary owner (depending on how `_require_owner` is implemented), this will fail.
- **Dual-purpose logic** — The function checks for `BoatCrew` first, then `PendingCrewInvite`. If a user is attempting to cancel an invite, they must ensure the `crew_id` matches the `PendingCrewInvite.id`.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and the `_require_owner` guard.
- **Websocket**: Emits `BOAT_CREW_UPDATED` for the specific `boat_id` upon successful deletion.
- **Side effects**: Triggers updates to any UI components listening for `BOAT_CREW_UPDATED`, such as the boat's crew list or member counts.

## External consumers

- `concorda-web` (via `boatApi.removeCrew`)
- `concorda-test` (via `ApiClient.removeCrewMember`)

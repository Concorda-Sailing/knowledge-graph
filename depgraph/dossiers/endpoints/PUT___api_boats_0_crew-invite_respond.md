---
node_id: PUT::/api/boats/{0}/crew-invite/respond
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ce87e977334cfdc7386ee256f6c93eabab8242feb52059e51e270a29cd7fdc4c
status: llm_drafted
---

# PUT /api/boats/{boat_id}/crew-invite/respond

## Purpose

Allows a user to accept or decline a pending crew invitation for a specific boat. This endpoint transitions a `BoatCrew` membership status from `invited` to either `active` or `declined`. It is distinct from the `coowner-request` endpoint, which initiates a promotion workflow rather than responding to an existing invite.

## Invariants

- **Method is `PUT`** — used for state transitions on an existing resource.
- **Requires `current_user` authentication** via `require_auth`.
- **Input `data.action` must be exactly `"accept"` or `"declined"`** — any other value results in a 400 Bad Request.
- **Membership must be in `invited` status** — if the user is already `active` or the status is `declined`, the API returns a 404.
- **Returns a JSON object** with a success message confirming the action taken.

## Gotchas

- **Status transition is critical for security.** Per commit `36ef425`, the system relies on the `invited` status to prevent unauthorized users from gaining access to boat data. If a user is not yet `active` or `prospective`, they should not have access to the boat's private details.
- **The `boat_id` must exist and the user must have a valid invite.** The function calls `_get_boat_or_404` and `_get_crew_membership` to validate the context before any state change occurs.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Websocket**: Emits `BOAT_CREW_UPDATED` event for the given `boat_id` upon successful commit.
- **Side effects**: Triggers updates to any UI components listening to boat crew changes (e.g., crew lists or boat detail views).

## External consumers

- `concorda-web` (via `boatApi.respondToInvite`)
- `concorda-test` (via `ApiClient.respondToBoatCrewInvite`)

---
node_id: GET::/api/profile/crew
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0c751c30e223a8e81c4e150ec13b07ac4423929c175b3112e89482c48c449fb2
status: current
---

# GET /api/profile/crew

## Purpose

Provides a comprehensive overview of a user's "crew" context. It aggregates all boats where the user is the `owner` (with `active` status) and includes the full crew roster for those boats, alongside any pending invitations the user has received. This is the primary endpoint for the "My Crew" dashboard, distinguishing itself from general boat-listing endpoints by nesting person-specific metadata (email, picture, name) and invitation status.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a list of boat objects**, where each boat contains a `crew` list and a `pending_invites` list.
- **Filters for ownership** — only boats where the user is an `owner` and the `BoatCrew` status is `active` are returned.
- **Includes person metadata** — the `crew` array includes `person_first_name`, `person_last_name`, `person_email`, and `person_picture_url` by joining the `Person` table.

## Gotchas

- **Self-subtraction logic** — per commit `aa25225`, ensure that logic does not accidentally subtract a user's own pending invite from the `open_positions` count, as this endpoint is a consumer of that logic.
- **Role-based visibility** — the endpoint specifically looks for `BoatCrew.role == "owner"` to establish the base list of boats; users who are merely members of a boat will not see that boat in this specific response.
- **Data integrity for person details** — if a `Person` record is missing or has a null `picture_url`, the API uses `getattr` and null-checks to return `None` rather than throwing a 500.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the `current_user`.
- **Side effects**: Changes to boat ownership or crew status (e.g., via `PUT /api/events/{0}/sailing-event/crew-pool`) will directly alter the shape and content of this response.

## External consumers

- `concorda-web` (via `profileApi.getMyCrew`)
- `concorda-test` (via `ApiClient.getMyCrewData`)

## Open questions

- Should the `pending_invites` logic be expanded to include invitations to join a boat as an `owner` vs a `member`, or is the current distinction sufficient for the UI?

---
node_id: GET::/api/boats/{0}/crew
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 041637eedda227de0191bc7adbd7986a2003cf289babf1f4dad7da1e9563eb66
status: current
---

# GET /api/boats/{boat_id}/crew

## Purpose

Returns a list of all crew members associated with a specific boat. This endpoint is the primary source of truth for the "Crew" section of a boat's detail view, providing both the person's identity and their current membership status. It is distinct from the `pending-invites` endpoint, which handles unauthenticated or non-account-holding users.

## Invariants

- **Requires `require_auth`** — The request must include a valid bearer token from an authenticated user.
- **Strict Authorization** — Access is restricted to users who are either the boat owner or an active/invited crew member.
- **Returns `list[BoatCrewRead]`** — The response is an array of objects containing the person's identity and membership status.
- **Dependency on `_get_boat_or_404`** — If the `boat_id` does not exist, the endpoint returns a 404 before checking membership.

## Gotchas

- **Membership status check** — Access is granted if the user's status is either `"active"` or `"invited"`. Per commit `36ef425`, the authorization logic was tightened to ensure a staged approval process doesn't inadvertently block access.
- **Identity mapping** — The function relies on `_crew_to_read` to join the `BoatCrew` record with the `Person` table. If a `Person` record is missing for a `person_uuid`, the behavior depends on the implementation of that helper.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and validates membership via `_get_crew_membership`.
- **Side effects**: Used by the boat-detail view to render the crew list.

## External consumers

- `concorda-web` (via `boatApi.getCrew`)
- `concorda-test` (via `ApiClient.getBoatCrew`)

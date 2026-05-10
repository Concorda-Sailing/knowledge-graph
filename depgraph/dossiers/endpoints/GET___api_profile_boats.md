---
node_id: GET::/api/profile/boats
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 771e443a15de0706398187f0f0d7a06c34131f82aebbb32889573e73c1271150
status: llm_drafted
---

# GET /api/profile/boats

## Purpose

Returns a list of all boats where the authenticated user holds an "owner" role. This is the primary endpoint for populating the user's personal boat dashboard and identifying which vessels they have administrative control over. It is distinct from the `/crew` endpoint, which provides a deeper view of members and pending invites; this endpoint is strictly for the high-level list of owned `Boat` objects.

## Invariants

- **Requires `require_auth`** — The request must include a valid session/token; otherwise, the `current_user` dependency fails.
- **Returns `list[BoatRead]`** — The response is a JSON array of boat objects conforming to the `BoatRead` schema.
- **Ownership filter is strict** — A boat is only returned if the user is explicitly linked via `BoatCrew` with `role == "owner"` and `status == "active"`.

## Gotchas

- **Role/Status dependency** — A user is not an "owner" of a boat unless their `BoatCrew` record has both `role == "owner"` and `status == "active"`. If a user is demoted or deactivated, they will silently disappear from this list.
- **Recent IDOR audit** — Per commit `c9a7c41`, this endpoint and its related profile endpoints were part of a tier-A IDOR audit to ensure users can only access their own boat ownership data.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to inject `current_user`.
- **Side effects**: Used by `profileApi.getBoats` in `concorda-web` to populate the user's primary vessel list.

## External consumers

- `concorda-web` (via `profileApi.getBoats`)
- `concorda-test` (via `ApiClient.getBoats`)

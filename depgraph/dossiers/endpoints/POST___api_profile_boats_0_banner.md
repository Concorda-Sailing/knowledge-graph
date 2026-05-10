---
node_id: POST::/api/profile/boats/{0}/banner
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 32c2cd3fce514509725055b38bbe9c6f0ed955dbef999d2d562284b65a2851ae
status: current
---

# POST /api/profile/boats/{boat_id}/banner

## Purpose

Uploads a new banner image for a specific boat. This endpoint is distinct from the `DELETE` counterpart which clears the banner. It is used by the boat configuration interface to allow owners to personalize their boat profile with a visual header.

## Invariants

- **Requires `current_user` ownership** — The request must pass `require_auth` and the `_owner_query` check to ensure only the boat's owner can modify the banner.
- **Input is a multipart file** — Expects an `UploadFile` object.
- **Max dimension is 1600px** — The `save_upload` call enforces a `max_dimension=1600` to prevent excessive storage usage.
- **Returns `BoatRead`** — On success, returns the updated boat object including the new `banner_url`.
- **Updates `boat.banner_url`** — The resulting URL is persisted to the database via `db.commit()`.

## Gotchas

- **Ownership check is mandatory** — Per `c9a7c41 security: tier-A IDOR audit fixes`, this endpoint relies on `_owner_query` to prevent unauthorized users from overwriting banners of boats they do not own.
- **Broadcasts updates** — Any change to the banner triggers a `BOAT_UPDATED` event via `broadcast_event(BOAT_UPDATED, boat.id)`.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_owner_query` to validate ownership.
- **Websocket**: Emits `BOAT_UPDATED` for the specific `boat_id`.
- **Side effects**: Triggers updates for any UI components listening to boat state changes (e.g., boat profile headers).

## External consumers

None known.

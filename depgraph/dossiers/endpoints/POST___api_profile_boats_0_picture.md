---
node_id: POST::/api/profile/boats/{0}/picture
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9c12b93b6c82d28ded7f64d0904aa00e84f79b0869756a482d30b24ddf932bdd
status: llm_drafted
---

# POST /api/profile/boats/{boat_id}/picture

## Purpose

Handles the uploading and deletion of a boat's profile picture. This endpoint is distinct from the banner endpoint (which uses a `max_dimension=1600` constraint) and is used to manage the primary visual identity of a boat within the platform.

## Invariants

- **Requires `require_auth`** — the user must be authenticated.
- **Ownership check is mandatory** — uses `_owner_query` to ensure the `current_user.id` matches the boat owner before any file operations or database mutations occur.
- **Returns `BoatRead`** — the response shape is the full boat object including the updated `picture_url`.
- **File handling** — uses `save_upload` to persist the file to the `boats` directory using the `boat_id` as the identifier.

## Gotchas

- **Security/IDOR protection** — per commit `c9a7c41` (tier-A IDOR audit fixes), this endpoint must strictly validate ownership via `_owner_query` to prevent unauthorized users from modifying boat assets.
- **Broadcast dependency** — any change to the picture (upload or delete) triggers a `BOAT_UPDATED` event via `broadcast_event`.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth` and a successful `_owner_query` check.
- **Websocket**: Emits `BOAT_UPDATED` event upon successful mutation.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Triggers updates to any UI component listening for `BOAT_UPDATED` for the specific `boat_id`.

## External consumers

None known.

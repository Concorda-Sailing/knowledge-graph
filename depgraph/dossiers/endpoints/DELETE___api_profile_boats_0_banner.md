---
node_id: DELETE::/api/profile/boats/{0}/banner
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c7b19114216454c17a8610215b30a72730ed31ceaa5034d695260897fe3f3e73
status: current
---

# DELETE /api/profile/boats/{boat_id}/banner

## Purpose

Removes the banner image associated with a specific boat. It clears the `banner_url` field in the database and invokes the deletion of the physical file from the storage provider. This is used when a user wants to reset or remove the visual branding of a boat profile.

## Invariants

- **Requires `require_auth`** — The user must be authenticated.
- **Ownership check is mandatory** — The request must pass the `_owner_query` check to ensure the `current_user.id` matches the boat's owner.
- **Returns `BoatRead`** — On success, returns the updated `Boat` object with `banner_url` set to `None`.
- **Deletes physical asset** — Calls `delete_upload("boat-banners", boat.id)` to ensure the storage is cleaned up alongside the database record.

## Gotchas

- **IDOR Protection** — Per commit `c9a7c41` (security: tier-A IDOR audit fixes), this endpoint relies on the `_owner_query` to prevent unauthorized users from deleting banners of boats they do not own.
- **Resource cleanup** — If the `delete_upload` call fails or is skipped, the database record is cleared but the file remains in storage; ensure any logic involving file deletion follows the same pattern as `save_upload` seen in the sibling `POST` method.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and validates ownership via `_owner_query`.
- **Websocket**: Emits `BOAT_UPDATED` for the given `boat_id` upon successful deletion.
- **Side effects**: Triggers updates to any UI component listening for `BOAT_UPDATED` (e.g., boat profile views or lists).

## External consumers

- `concorda-web` (via `profileApi.deleteBoatBanner`)

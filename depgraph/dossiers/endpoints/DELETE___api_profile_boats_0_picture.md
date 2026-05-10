---
node_id: DELETE::/api/profile/boats/{0}/picture
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a500b688dde8535703b144d94c2344fc796446801d73bb3ac95c1fee4e6f86b
status: llm_drafted
---

# DELETE /api/profile/boats/{boat_id}/picture

## Purpose

Removes the profile picture associated with a specific boat. This endpoint is used to clear the `picture_url` field in the database and delete the corresponding file from storage. It is distinct from the banner deletion endpoint, which handles the `banner_url` field.

## Invariants

- **HTTP Method is `DELETE`**.
- **Requires `current_user` authentication** via `require_auth`.
- **Ownership check is mandatory**: The request must pass the `_owner_query` check, ensuring the authenticated user is the owner of the boat before any deletion occurs.
- **Returns the updated `BoatRead` object** with `picture_url` set to `None`.
- **Deletes from the "boats" storage path** via `delete_upload("boats", boat.id)`.

## Gotchas

- **IDOR Protection**: Per commit `c9a7c41` (`security: tier-A IDOR audit fixes`), this endpoint relies on the `_owner_query` to prevent unauthorized users from deleting boat assets. Ensure any modifications to the ownership logic do not bypass this check.
- **Broadcast Side Effects**: Deleting the picture triggers a `BOAT_UPDATED` event via `broadcast_event`. If a client is listening for boat updates, they will receive a notification that the boat state has changed even though only the image was removed.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_owner_query` to validate ownership.
- **Websocket**: Emits `BOAT_UPDATED` for the specific `boat_id`.
- **Side effects**: Triggers updates to any UI components or services monitoring the `Boat` object state.

## External consumers

- `concorda-web` (via `profileApi.deleteBoatPicture`)

---
node_id: DELETE::/api/profile/boats/{0}/resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5775296b0eb19bc83dee13eb873bea11cea8dbb6eda10dda7137de6fe6d9ff6e
status: llm_drafted
---

# DELETE /api/profile/boats/{boat_id}/resume

## Purpose

Deletes the `BoatResume` associated with a specific boat. This is a destructive action used to clear out sailing credentials and professional data for a boat. It is distinct from boat configuration edits; it removes the entire resume entity rather than just modifying fields.

## Invariants

- **HTTP Method is `DELETE`**.
- **Requires `boat_id`** in the URL path.
- **Auth is mandatory** via `require_auth`.
- **Ownership check is required**: The `current_user` must pass the `_owner_query` check for the specific `boat_id` to prevent unauthorized deletions.
- **Returns a success message** `{"message": "Boat resume deleted successfully"}` upon successful deletion.
- **Throws 404** if the boat does not exist or if no resume is currently associated with the boat.
- **Throws 403** if the authenticated user is not the owner of the boat.

## Gotchas

- **Security/IDOR protection**: Per commit `c9a7c41` (security: tier-A IDOR audit fixes), this endpoint relies on `_owner_query` to ensure users cannot delete resumes for boats they do not own.
- **Strict dependency on `boat_id`**: If the `boat_id` is valid but the `BoatResume` record has already been removed or never existed, the API returns a 404 rather than a 204 or 200.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_owner_query` to enforce ownership.
- **Websocket**: Emits `BOAT_RESUME_DELETED` event with the `boat_id` payload.
- **Side effects**: Deleting the resume may affect any UI components or views that rely on displaying the boat's professional credentials/sailing resume.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.deleteBoatResume`

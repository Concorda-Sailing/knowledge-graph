---
node_id: DELETE::/api/profile/picture
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17fd4013bd547e1f7b9309645247f56c0705f048f8a7a3ab9db0dcb8da77fcb6
status: current
---

# DELETE /api/profile/picture

## Purpose

Removes the profile picture for the authenticated user. It clears the `picture_url` field in the database and triggers a deletion of the associated file in the "people" storage bucket. Use this instead of the `POST` endpoint when a user wants to reset their profile image to a default state.

## Invariants

- **HTTP Method**: `DELETE`
- **Auth**: Requires a valid session via `require_auth`.
- **Return Shape**: Returns the updated `ProfileRead` object (the `Person` model) with `picture_url` set to `null`.
- **Storage Path**: Deletes the file from the `"people"` directory/bucket using the user's ID.

## Gotchas

- **Dependency on `delete_upload`**: This endpoint relies on `delete_upload("people", user.id)` to clean up the physical file. If the file is not in the `"people"` path, the function must handle the missing file gracefully to avoid 500 errors.
- **Broadcast Requirement**: Must call `broadcast_event(PERSON_UPDATED, user.id)` after the DB commit to ensure the UI reflects the absence of the image.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth`.
- **Websocket**: Emits `PERSON_UPDATED` via `broadcast_event`.
- **Audit**: N/A
- **Rate limit**: None.
- **Side effects**: Triggers a refresh of any UI component displaying the user's profile picture (e.g., navigation bars, profile settings page).

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.deletePicture`

---
node_id: POST::/api/profile/picture
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c6fff5dc8a987ae6ad17ae1caeea2f83dcdca77c7ac2dff6dd5a6fd6d662162
status: current
---

# POST /api/profile/picture

## Purpose

Handles the uploading and deletion of a user's profile picture. This endpoint manages the file-to-URL mapping by saving the uploaded file to the `people` directory and updating the `picture_url` field on the `Person` model. It is distinct from the banner endpoints, which store data within the `meta` JSON field rather than a top-level column.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a `ProfileRead` schema** containing the updated user object.
- **Uses the `save_upload` helper** to persist the file to the `people` storage path.
- **Updates the `Person.picture_url` field** directly in the database.

## Gotchas

- **Recent security hardening:** Per commit `ec53704`, ensure that any logic modifying user-related state (like profile updates) is strictly gated by authentication to prevent unauthorized DB writes.
- **Broadcast dependency:** This endpoint triggers a `PERSON_UPDATED` event via `broadcast_event`. Any change to the profile picture will trigger downstream updates for any service listening for person-level changes.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user session).
- **Websocket**: Emits `PERSON_UPDEDATED` event upon successful upload or deletion.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Triggers updates for any UI component or service tracking the `PERSON_UPDATED` event for the specific `user.id`.

## External consumers

None known.

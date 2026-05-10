---
node_id: DELETE::/api/profile/banner
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c9277f42413e203009d470b9efa2a4caf46ce74ac29f8d5587c0ce2fd43ae7ae
status: llm_drafted
---

# DELETE /api/profile/banner

## Purpose

Removes the banner image associated with the current user's profile. It performs a two-step cleanup: deleting the physical file from the storage provider via `delete_upload` and removing the `banner_url` key from the user's metadata dictionary. This is the inverse of the banner upload logic and ensures that a user can revert to a default profile state.

## Invariants

- **Method is `DELETE`** — targets the `/api/profile/banner` endpoint.
- **Requires authentication** — uses `require_auth` to identify the `current_user`.
- **Clears `user.meta["banner_url"]`** — the key is popped from the dictionary, not just set to null.
- **Triggers a broadcast** — emits the `PERSON_UPDATED` event for the specific user ID.
- **Returns the updated `User` object** — the response body follows the `ProfileRead` model.

## Gotchas

- **`delete_upload` is side-effect heavy** — the function calls `delete_upload("people-banners", user.id)`. If the storage provider is unreachable or the file doesn't exist, ensure the implementation of `delete_upload` is idempotent to prevent 500 errors during the deletion process.
- **Deepcopy requirement** — the function uses `_copy.deepcopy(dict(user.meta or {}))` to avoid mutating the live SQLAlchemy object before the commit is finalized.

## Cross-cutting concerns

- **Auth**: Requires a valid session via `require_auth`.
- **Websocket**: Emits `PERSON_UPDATED` via `broadcast_event`. This may trigger UI updates for any component observing the user's profile state.
- **Audit**: N/A.
- **Rate limit**: None explicitly defined for this endpoint in the recent history.
- **Side effects**: The `PERSON_UPDATED` broadcast ensures that any active sessions or dashboards displaying the user's profile (including the banner) refresh to reflect the absence of the image.

## External consumers

- `concorda-web` (via `profileApi.deleteBanner`)

---
node_id: POST::/api/profile/banner
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6002adaf6eb675226b01b15cd2e71606b74263caca56afa0143ef5ea469878cf
status: current
---

# POST /api/profile/banner

## Purpose

Handles the uploading and deletion of a user's profile banner image. This endpoint manages the `banner_url` field within the `meta` JSON blob of the `Person` record. It is distinct from general profile updates as it specifically handles file uploads via `save_upload` and manages the lifecycle of the banner asset.

## Invariants

- **Method is `POST`** — used for both uploading (creating/replacing) and deleting (via the logic in the source).
- **Requires `current_user`** — authenticated via `require_auth`.
- **Updates `user.meta["banner_url"]`** — the URL is stored as a string within the person's metadata dictionary.
- **Returns `ProfileRead`** — the response is the full updated user object.
- **Uses `people-banners` storage prefix** — all uploads and deletions are scoped to this directory/prefix.

## Gotchas

- **Deepcopy required for meta updates** — the implementation uses `_copy.deepcopy(dict(user.meta or {}))` to ensure the metadata dictionary is mutated safely without side-effecting the original object before the commit.
- **`PERSON_UPDATED` broadcast** — any change to the banner triggers a `broadcast_event(PERSON_UPDATED, user.id)`, which may trigger downstream UI refreshes for any component observing that user.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` to identify the `current_user`.
- **Websocket**: Emits `PERSON_UPDATED` event upon successful upload or deletion.
- **Side effects**: Triggers updates to any UI component observing the user's profile (e.g., profile headers or user detail views).

## External consumers

None known.

## Open questions

- The current implementation uses `import copy as _copy` inside the function body; should this be moved to the module level to follow standard PEP8 patterns, or is the local import intentional to minimize overhead for non-banner calls?

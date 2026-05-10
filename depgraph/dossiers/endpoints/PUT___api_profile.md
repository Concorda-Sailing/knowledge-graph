---
node_id: PUT::/api/profile
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b43792c02647675239384773b62a88bab201cbcf55e089ce714c948acf6e1fea
status: current
---

# PUT /api/profile

## Purpose

Updates the authenticated user's profile data. It handles partial updates for nested `preferences` and `meta` dictionaries to ensure that updating one key doesn't wipe out the entire object. Use this endpoint when a user modifies personal details like contact info, shirt size, or club affiliations.

## Invariants

- **Requires `AuthUser`** — The endpoint is protected by `require_auth`.
- **Returns `ProfileRead`** — The response shape is a serialized version of the `Person` model.
- **Strict field whitelist** — Only fields defined in `PROFILE_ALLOWED_FIELDS` (e.g., `first_name`, `mailing_address`, `preferences`) are applied to the database.
- **Partial updates for nested objects** — `preferences` and `meta` are merged rather than overwritten.

## Gotchas

- **Nested dictionary merging** — The function performs a deep merge for `preferences` and `meta`. If you pass a dictionary for a section, it updates existing keys rather than replacing the whole section.
- **`exclude_unset=True` logic** — The implementation relies on `model_dump(exclude_unset=True)` to distinguish between a field being "missing" from the request versus "explicitly null."
- **Recent regression in boat-config** — Per commit `d54327b`, there was a revert regarding how changes cascade to snapshots/assignments. Ensure profile updates do not inadvertently trigger unintended side effects in the boat-config-related snapshots.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` dependency.
- **Websocket**: Emits `PERSON_UPDATED` on any profile change; emits `DIRECTORY_CHANGED` specifically if the `preferences` field is included in the update.
- **Audit**: N/A.
- **Rate limit**: N/A (Note: `_change_password_rate_limit` is defined in this file but applies to the `/change-password` sub-route, not this base path).
- **Side effects**: Profile changes may trigger updates to the user's visible identity across the platform via the `PERSON_UPDATED` event.

## External consumers

- `concorda-web` (via `profileApi.update`)
- `concorda-test` (via `ApiClient.updateProfile`)

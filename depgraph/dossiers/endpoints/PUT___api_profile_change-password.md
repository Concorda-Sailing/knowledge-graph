---
node_id: PUT::/api/profile/change-password
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf0d6fe77649a5541b9f65f8443008d05719b25eb1f17d44acba482031decfde
status: llm_drafted
---

# PUT /api/profile/change-password

## Purpose

Updates the current user's password. It requires the `current_password` to be verified against the existing `password_hash` before allowing a change. This endpoint is distinct from the login flow as it acts as a secondary gate for identity verification during a session.

## Invariants

- **Method is `PUT`** to `/api/profile/change-password`.
- **Requires `require_auth`** via the `current_user` dependency.
- **Input must be a `ChangePasswordRequest`** containing `current_password` and `new_password`.
- **Invalidates all existing `AuthToken`s** for the user upon successful change.
- **Returns a success message** and requires the client to re-authenticate to establish a new session.

## Gotchas

- **Rate limiting is per-user, not per-IP.** The `_change_password_rate_limit` uses `current_user.id` to prevent brute-forcing the `current_password` gate. This is a critical security measure because the standard `/login` IP-based limits do not apply here.
- **Environment-specific behavior:** Rate limiting is skipped if `CONCORDA_ENV` is set to `"test"`.
- **Session termination:** Because this endpoint deletes all `AuthToken` entries for the `person_id`, any active sessions on other devices (mobile, web, etc.) will be immediately invalidated.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the user is logged in.
- **Rate limit**: Implements a window of 900 seconds (15 minutes) with a maximum of 10 attempts per user via `_CHANGE_PW_RATE_LIMIT_MAX`.
- **Side effects**: Deletes all `AuthToken` records associated with the user in the database.

## External consumers

- `concorda-web` (via `profileApi.change-password`).

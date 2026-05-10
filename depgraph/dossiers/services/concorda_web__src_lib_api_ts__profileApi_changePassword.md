---
node_id: concorda-web::src/lib/api.ts::profileApi.changePassword
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 770a825dcdcb10a605622eb98ef5e2de5777ede7e918e7fab489cb532063ad85
status: llm_drafted
---

# profileApi.changePassword

## Purpose

Provides a method to update a user's password via the profile API. It is a specialized part of the `profileApi` service used to transition a user from an old password to a new one. Use this when a user is interacting with a "Change Password" form in the account settings.

## Invariants

- **HTTP Method is `PUT`** — The request must use `PUT` to the `/api/profile/change-password` endpoint.
- **Requires `fetchApiAuthenticated`** — This method relies on the authenticated session to identify the user.
- **Payload structure** — The body must be a JSON string containing exactly `current_password` and `new_password`.
- **Returns a success message** — The expected return shape is `{ message: string }`.

## Gotchas

- **Authentication dependency** — Because it uses `fetchApiAuthenticated`, the user must have a valid, non-expired session. If the session is lost or the token is invalid, this will fail with a 401/403 error.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Rate limit**: none

## External consumers

None known.

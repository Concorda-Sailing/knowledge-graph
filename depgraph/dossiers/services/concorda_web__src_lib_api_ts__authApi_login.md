---
node_id: concorda-web::src/lib/api.ts::authApi.login
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9863cc3d2eb5879e6ce1d3f1e7082cc649ec44d72a05ec014d3349b0caecfaf5
status: llm_drafted
---

# authApi.login

## Purpose

The primary authentication method for the web application. It posts credentials to `/api/auth/login` to establish a session and returns the access token and token type. Use this method when a user needs to establish a full authenticated session for the application.

## Invariants

- **Method is `POST`** to `/api/auth/login`.
- **Returns a JSON object** containing `{ access_token: string; token_type: string }`.
- **Accepts a `remember_me` boolean** to control token longevity/persistence.
- **Uses `fetchApi`** which handles the underlying request-to-response lifecycle.

## Gotchas

- **`auth-context.tsx` dependency**: This method is the primary driver for the `AuthProvider` (see `auth-context.tsx:164`). Changes to the return shape will break the global authentication state.
- **`register` vs `login` flow**: While `login` is for existing users, the `register` method (line 151) returns a `requires_verification` flag and an `access_token`, which may change the expected post-registration UX.

## Cross-cutting concerns

- **Auth**: Primary entry point for establishing the bearer token used by `fetchApiAuthenticated`.
- **Side effects**: Successful login/session establishment drives the state of the `AuthProvider` in `src/contexts/auth-context.tsx`.

## External consumers

None known.

---
node_id: concorda-web::src/lib/api.ts::authApi.setupAccount
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a82b91306ab1ce0dd0c4fb2013ac231061545214278dc1086289dd534dff1df6
status: current
---

# authApi.setupAccount

## Purpose

Finalizes a user's account creation by linking a provided token to a password. This is used during the onboarding flow after a user has been invited or registered but before they have established a full authenticated session. It is distinct from `register` (which creates the initial identity) and `login` (which establishes the session).

## Invariants

- **Method is `POST`** to `/api/auth/setup-account`.
- **Requires a `token` and `password`** in the JSON body.
- **Returns a full authentication object** containing `{ access_token, token_type }`.
- **The `token` is a single-use setup token** used to bridge the gap between identity creation and session establishment.

## Gotchas

- **Ordering is critical** — This must be called after the initial registration/invite step but before the user can access authenticated routes like `me` or `invite/accept`.
- **The response is a direct replacement for a login flow** — The returned `access_token` should be used to establish the authenticated state in the client, similar to the return shape of `authApi.login`.

## Cross-cutting concerns

- **Auth**: Returns the credentials required to transition from a "setup" state to an "authenticated" state.
- **Side effects**: Successful completion of this call is a prerequisite for the user to interact with `inviteApi.acceptInvite` and view protected dashboard content.

## External consumers

- `concorda-web::src/app/setup-account/page.tsx` (SetupAccountContent)

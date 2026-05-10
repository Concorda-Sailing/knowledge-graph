---
node_id: concorda-web::src/lib/api.ts::authApi.logout
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c544ea2dc9c46f6ab77ca8b31897f086f2959de12df455c127f0d8cdf8f82cb1
status: llm_drafted
---

# authApi.logout

## Purpose

Terminates the current user session by calling the `/api/auth/logout` endpoint. It is a specialized method within `authApi` used to clear the authenticated state on the server and, by extension, the client.

## Invariants

- **Method is `POST`** — The endpoint requires a POST request to ensure the logout action is an intentional state change.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the request includes the bearer token; an unauthenticated call will fail.
- **Returns a message** — The expected response shape is `{ message: string }`.

## Gotchas

- **Session lifecycle dependency** — Because this is used by `AuthProvider` (see `auth-context.tsx:173`), calling this will trigger a global state change that affects all components relying on the `AuthContext`.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to attach the bearer token.
- **Side effects**: Triggers the unmounting/resetting of the `AuthProvider` state in `concorda-web::src/contexts/auth-context.tsx`.

## External consumers

- `concorda-web::src/contexts/auth-context.tsx` (via `AuthProvider`)

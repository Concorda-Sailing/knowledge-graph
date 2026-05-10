---
node_id: concorda-web::src/lib/api.ts::fetchApiAuthenticated
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 449f7097917b3b24854a4ccfd4818679bde2b7397f3f24b4df41b6787727766c
status: llm_drafted
---

# fetchApiAuthenticated

## Purpose

A specialized wrapper for the standard `fetch` call that automatically injects the Bearer token into the `Authorization` header. It is used for all authenticated API requests to ensure the client identity is correctly propagated. Use this instead of `fetchApi` when the endpoint requires user-level authorization.

## Invariants

- **Requires a valid token.** If `getAuthToken()` returns a falsy value, the function throws a hard `Error("Not authenticated")`.
- **Injects `Authorization: Bearer <token>` header.** This is appended to any existing headers provided in the `options` object.
- **Returns a Promise of type `T`.** The caller is responsible for defining the expected response shape.

## Gotchas

- **Strict Authentication Requirement.** Unlike `fetchApi`, this method will fail immediately if the user is not logged in. This is a critical distinction for components that might attempt to pre-fetch data during a loading state before the auth state is fully resolved.
- **Header Merging.** The `Authorization` header is injected via spread operator (`...options?.headers`). If a caller manually provides an `Authorization` header in the `options` object, the `Bearer` token from `getAuthToken()` will overwrite it.

## Cross-cutting concerns

- **Auth**: Depends on `getAuthToken()` for the bearer string.
- **Side effects**: Failure to call this (or a failure in the token retrieval) will prevent data from loading in features like the "incoming co-owner invites" (per commit `e02996c`) or any protected dashboard views.

## External consumers

None known.

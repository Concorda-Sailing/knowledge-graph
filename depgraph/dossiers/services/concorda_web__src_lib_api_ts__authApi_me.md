---
node_id: concorda-web::src/lib/api.ts::authApi.me
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bff3a49b545672de10ed9573d22c6c389729beca50c0491a399ea22c70f1af9b
status: current
---

# authApi.me

## Purpose

Fetches the authenticated user's profile information from the `/api/auth/me` endpoint. It is the primary method for retrieving the current session's identity and permissions, returning an `AuthUser` object. This is used to drive the global authentication state in the application.

## Invariants

- **Requires authentication** — Uses `fetchApiAuthenticated`, meaning a valid bearer token must be present in the request headers.
- **Returns `AuthUser`** — The response shape is strictly tied to the `AuthUser` interface.
- **Single source of truth** — The data returned here populates the global user context used by the rest of the application.

## Gotchas

- **Lightweight payload design** — Per the comment at `api.ts:253`, this endpoint is intentionally kept lightweight. Any additional data regarding policy acceptance (e.g., `PendingPolicy`) is fetched lazily via a separate call to `/policies/accept` to avoid bloating this call.
- **Dependency on `AuthProvider`** — The `AuthProvider` in `auth-context.tsx` (specifically at `auth-context.tsx:68`) relies on this call to initialize the user state; if this fails or returns an unexpected shape, the entire auth-driven UI tree will fail to mount.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Side effects**: The result of this call drives the visibility of protected routes and the identity-specific UI components (e.g., user profile displays and permission-gated buttons).

## External consumers

- `concorda-web::src/contexts/auth-context.tsx::AuthProvider`

## Open questions

- Should the `PendingPolicy` state be integrated into the `AuthUser` shape if the policy acceptance becomes a frequent blocking step, or should it remain a separate lazy-load to keep this endpoint fast?

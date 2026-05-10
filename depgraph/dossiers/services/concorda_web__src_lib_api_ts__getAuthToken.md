---
node_id: concorda-web::src/lib/api.ts::getAuthToken
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f1a85c5697dfd27de47095bdbccdbdd2d205bb12b224bd4977db180be1856ebe
status: current
---

# getAuthToken

## Purpose

Retrieves the current authentication token from the browser's `localStorage`. It serves as the low-level source of truth for identity in the web app, providing the string used by `fetchApiAuthenticated` to populate the `Authorization` bearer header.

## Invariants

- **Returns `string | null`**. Returns `null` if the `window` object is undefined (SSR safety) or if the key `auth_token` is missing.
- **Storage key is `auth_token`**. All authentication-related state is tied to this specific key in `localStorage`.
- **Client-side only**. Because it accesses `localStorage`, it returns `null` in non-browser environments to prevent runtime errors during server-side rendering.

## Gotchas

- **SSR/Hydration mismatch**: Because it returns `null` when `typeof window === "undefined"`, components relying on this for initial state must handle the transition from `null` to a string once the client hydrates to avoid hydration mismatch errors.
- **`authedUrl` dependency**: The `authedUrl` function relies on this to append the token as a query parameter (`?token=...`). If the token is cleared from `localStorage` but the component doesn't re-render, broken image links or media-access errors will persist.

## Cross-cutting concerns

- **Auth**: Primary source for the `Authorization: Bearer <token>` header in `fetchApiAuthenticated`.
- **Side effects**: Used by `AuthProvider` in `auth-context.tsx` to initialize the authenticated state of the application.

## External consumers

None known.

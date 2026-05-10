---
node_id: concorda-web::src/lib/api.ts::fetchApi
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b9910517ce1da6c69b051d522e18e7f6101a3af4417d08cc1cf86ffaebf9eb2
status: current
---

# fetchApi

## Purpose

The base fetch utility for the web application. It wraps the native `fetch` API to provide standardized error handling via `ApiError` and ensures a consistent `Content-Type: application/json` header. Use `fetchApi` for public/unauthenticated endpoints and `fetchApiAuthenticated` for any request requiring a Bearer token.

## Invariants

- **Base URL is absolute.** All `endpoint` arguments are appended to `API_BASE_URL`.
- **Defaults to JSON.** Automatically sets `Content-Type: application/json` unless overridden by `options`.
- **Returns `undefined` on 204.** If the status is `204 No Content`, the function returns `undefined` rather than attempting to parse a non-existent body.
- **Error shape is polymorphic.** If the response is not `ok`, it attempts to extract a `detail` field from the JSON body to populate the `ApiError`.

## Gotchas

- **Error detail extraction is fragile.** The function looks for `body.detail` or `body.detail.message`. If the API returns an error shape without these specific keys, the `message` defaults to the status text (e.g., "Internal Server Error").
- **`authedUrl` is required for media.** When displaying images/assets that require authentication, you must use `authedUrl` to append the token as a query parameter, otherwise, the browser will request the asset without credentials.

## Cross-cutting concerns

- **Auth**: `fetchApiAuthenticated` relies on `getAuthToken`, which pulls from `localStorage.getItem("auth_token")`. If the token is missing, it throws a hard `Error("Not authenticated")`.
- **Side effects**: Changes to the auth token in `localStorage` (via login/logout) will immediately change the behavior of all subsequent `fetchApiAuthenticated` calls.

## External consumers

None known.

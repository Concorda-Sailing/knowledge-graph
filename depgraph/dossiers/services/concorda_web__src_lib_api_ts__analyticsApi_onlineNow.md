---
node_id: concorda-web::src/lib/api.ts::analyticsApi.onlineNow
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 367225b46f82020dc77ef67d88a8a07c899425f1d80d225270bf5dbae58e07c3
status: current
---

# analyticsApi.onlineNow

## Purpose

Fetches the current list of users actively connected to the platform. It is a specialized endpoint within the `analyticsApi` group used to provide real-time presence visibility. Use this when building administrative or monitoring views that require a snapshot of current user activity, rather than historical trends provided by `summary` or `dailyActivity`.

## Invariants

- **Method/Path**: Performs a `GET` request to `/api/analytics/online-now`.
- **Authentication**: Requires a valid bearer token via `fetchApiAuthenticated`.
- **Return Shape**: Returns an array of `OnlineUser[]`.
- **No Parameters**: The endpoint accepts no arguments or query parameters.

## Gotchas

- **Real-time vs. Historical**: Unlike `dailyActivity` or `summary`, this does not accept `start` or `end` ISO strings. Attempting to pass time bounds to this function will result in a type error or a failed fetch, as the underlying endpoint is strictly for the current instant.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure only authorized users (typically admins) can view active user presence.
- **Side effects**: Directly drives the `AnalyticsContent` component in the admin dashboard.

## External consumers

- concorda-web::src/app/members/admin/analytics/page.tsx (AnalyticsContent)

## Open questions

- Should the response include more granular metadata (e.g., device type or last active timestamp) to provide better context for the admin dashboard?

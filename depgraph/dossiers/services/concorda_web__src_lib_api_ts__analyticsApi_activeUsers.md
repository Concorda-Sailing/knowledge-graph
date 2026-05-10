---
node_id: concorda-web::src/lib/api.ts::analyticsApi.activeUsers
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2d4a62cf8d0bce2c1f2af748b8abfbadaecce0a2f6bf167a816677a663a631ac
status: current
---

# analyticsApi.activeUsers

## Purpose

Retrieves a list of active users within a specific time range. It is a specialized method of the `analyticsApi` service used to track user engagement and presence. Use this when you need to populate administrative dashboards or engagement reports that require a temporal view of user activity.

## Invariants

- **Requires `start` and `end` parameters** as ISO strings to define the temporal window.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to execute.
- **Returns an array of `ActiveUser[]` objects.**
- **Time-range dependent** — the result set is strictly bounded by the provided `start` and `end` strings.

## Gotchas

- **Temporal precision depends on input format.** While the function accepts strings, the backend expects valid ISO-8601 timestamps to correctly filter the activity-log-based user presence.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Side effects**: Directly populates the `AnalyticsContent` component in the admin members page.

## External consumers

- `concorda-web::src/app/members/admin/analytics/page.tsx` (AnalyticsContent component).

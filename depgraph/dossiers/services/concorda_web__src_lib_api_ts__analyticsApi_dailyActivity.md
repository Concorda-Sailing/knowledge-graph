---
node_id: concorda-web::src/lib/api.ts::analyticsApi.dailyActivity
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 212b7230f8ed937a3342598b54d04c21dbc605047cb375b98e58e08374dc230c
status: llm_drafted
---

# analyticsApi.dailyActivity

## Purpose

Fetches time-series activity data for the organization. It provides a list of `DailyActivity` objects representing user engagement over a specified date range. This is used by the admin dashboard to visualize engagement trends. Use this instead of `summary` when you need to plot a chart over time rather than just seeing aggregate totals.

## Invariants

- **Requires `start` and `end` strings.** Both parameters must be provided as valid date strings (typically ISO format) to define the temporal bounds of the query.
- **Uses `fetchApiAuthenticated`.** All calls must be made through the authenticated helper to ensure the bearer token is attached.
- **Returns `DailyActivity[]`.** The response is an array of objects containing activity counts for specific timestamps.

## Gotchas

- **Dependency on `fetchApiAuthenticated`.** If the underlying authentication mechanism or the `API_BASE_URL` changes, this method will fail to resolve.
- **Admin-only access.** While not explicitly in the function signature, the `AnalyticsContent` component (the primary consumer) is located in the `/admin/` route, implying these endpoints are protected by admin-level permissions.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Data is consumed by the `AnalyticsContent` component in the admin dashboard to render engagement charts.

## External consumers

- `concorda-web::src/app/members/admin/analytics/page.tsx` (AnalyticsContent component).

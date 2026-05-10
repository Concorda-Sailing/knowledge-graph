---
node_id: concorda-web::src/lib/api.ts::analyticsApi.summary
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a4766580325b1039c2bf60e8e36dfd96eb8e6e73fd15cab03dc3c1432ae5af9
status: current
---

# analyticsApi.summary

## Purpose

Provides access to high-level organizational metrics and real-time user activity. This service is used to populate administrative dashboards that require time-bounded statistical views (e.g., `summary`, `topEndpoints`, `dailyActivity`) or real-time presence data (`onlineNow`). Use this when you need to visualize system-wide trends or current engagement levels rather than specific entity data.

## Invariants

- **Requires authentication.** Every method calls `fetchApiAuthenticated`, meaning a valid bearer token must be present in the session.
- **Time-bounded queries.** The `summary`, `topEndpoints`, `activeUsers`, and `dailyActivity` methods all require `start` and `end` ISO strings to define the temporal window for the requested data.
- **Returns typed interfaces.** Methods return specific shapes like `AnalyticsSummary`, `EndpointStat[]`, `ActiveUser[]`, or `DailyActivity[]`.

## Gotchas

- **Admin-only visibility.** While the code doesn't explicitly check roles, the `AnalyticsContent` component (the primary consumer) is part of the `/members/admin/` path, implying these endpoints are intended for administrative views.
- **Temporal dependency.** The `start` and `end` parameters must be valid ISO strings; passing malformed strings or incorrect formats will likely result in API errors or empty datasets.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` for all calls.
- **Side effects**: Data returned here is used to drive the `AnalyticsContent` view in the admin dashboard.

## External consumers

- `concorda-web::src/app/members/admin/analytics/page.tsx` (AnalyticsContent component).

---
node_id: GET::/api/analytics/daily-activity
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ca35a4deef7f9b8cb571cdcd99c9d81d244adc0dc563d5f6a91675e811f711dd
status: llm_drafted
---

# GET /api/analytics/daily-activity

## Purpose

Provides time-series data for user activity to drive dashboard visualizations. It aggregates `ActivityLog` entries by day, calculating both total request counts and unique user counts. The endpoint ensures a continuous data series by padding missing dates with zero-values, preventing breaks in frontend charting components.

## Invariants

- **Method/Path**: `GET /api/analytics/daily-activity`.
- **Auth**: Requires `org_admin` or `system_admin` roles via `require_any_role`.
- **Input**: Accepts optional `start` and `end` date query parameters.
- **Output Shape**: Returns a list of objects containing `date` (ISO string), `requests` (integer), and `users` (integer).
- **Data Continuity**: The response must include every day between `since` and `until` (inclusive), even if no activity occurred, to ensure the frontend chart does not skip intervals.

## Gotchas

- **Date Windowing**: The `_resolve_window` helper determines the default range; if `start` and `end` are not provided, it defaults to a 30-day window.
- **Implicit Dependency**: The density of the returned list depends on the `ActivityLog` table. If the logging middleware (added in commit `7c1ad77`) fails to record events, this endpoint will return zeros despite active user sessions.

## Cross-cutting concerns

- **Auth**: Guarded by `require_any_role("org_admin", "system_admin")`.
- **Side effects**: Data is derived directly from the `ActivityLog` table; any changes to the logging schema or the `ActivityLog.created` field will break the aggregation.

## External consumers

- `concorda-web` (via `analyticsApi.dailyActivity`)

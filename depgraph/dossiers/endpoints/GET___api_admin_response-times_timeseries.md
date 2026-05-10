---
node_id: GET::/api/admin/response-times/timeseries
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 015676f4aef1448b51ef9b272860a836c457c2249f96c2ea80a86c5d390dc3ff
status: current
---

# GET /api/admin/response-times/timeseries

## Purpose

Provides time-bucketed latency metrics for a specific API endpoint (identified by `method` and `path`). It calculates the p50, p95, and max duration, alongside error counts, to help administrators diagnose performance degradation or high-latency spikes in specific routes. It is distinct from general system health checks as it drills down into the `activity_log` for granular, path-specific investigation.

## Invariants

- **Requires `current_user` with system admin privileges** via the `_require_system_admin` guard.
- **Returns a list of `ResponseTimeBucket` objects** containing `bucket_start` (ISO UTC string), `count`, `p50_ms`, `p95_ms`, `max_ms`, and `error_count`.
- **Buckets are aligned to epoch boundaries** using the `bucket_seconds` calculation to ensure stable time-series visualization.
- **Input `hours` is capped** between 1 and 168 (one week) to prevent massive queries on the `activity_log`.

## Gotchas

- **Complexity of the SQL window functions:** The calculation of `p50` and `p95` relies on `ROW_NUMBER()` and `COUNT(*) OVER` within the `activity_log` table. Changes to the `activity_log` schema or the way `duration_ms` is recorded will break the statistical accuracy.
- **Performance risk on large datasets:** Because this performs heavy aggregation (including `MAX(CASE...)` and `ROW_NUMBER()`) over a potentially large `activity_log`, high `hours` values or small `bucket_minutes` can lead to slow response times.
- **Recent history of admin endpoint instability:** The recent history shows a pattern of rapid changes and reverts in admin endpoints (e.g., `1c61ff5` revert and `5b632f2` re-implementation of user management). While this specific endpoint is for response times, the `admin` router as a whole is a high-churn area for security and access control.

## Cross-cutting concerns

- **Auth**: Requires `_require_system_admin` (System Admin level).
- **Audit**: Reads from the `activity_log` table.
- **Side effects**: Used by the admin dashboard to visualize API health and latency-driven regressions.

## External consumers

- `concorda-web` (specifically `adminHealthApi.responseTimesTimeseries` in `api.ts`).

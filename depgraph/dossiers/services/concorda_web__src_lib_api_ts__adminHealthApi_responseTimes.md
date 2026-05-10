---
node_id: concorda-web::src/lib/api.ts::adminHealthApi.responseTimes
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f6458734c5b9d983bb3a75e72f43aa9c39a334259a4fe0977dc15327a10612e3
status: llm_drafted
---

# adminHealthApi.responseTimes

## Purpose

Provides access to API endpoints for monitoring system performance and database health. It is used to fetch raw response time data, time-series buckets, and specific request logs for administrative troubleshooting. This is distinct from `adminOrgConfigApi`, which handles configuration and assets; `adminHealthApi` is strictly for telemetry and diagnostic data.

## Invariants

- **Uses `fetchApiAuthenticated`** — All calls require a valid authenticated session.
- **Returns `ResponseTimeRow[]`** — The base `responseTimes` method returns an array of objects containing `duration_ms`, `status_code`, and `person_uuid`.
- **Query parameters are optional** — `hours` and `min_count` in `responseTimes` are not strictly required by the signature, but the function handles their string conversion for the URL.
- **Path-based filtering** — The `responseTimesTimeseries` and `responseTimesRequests` methods require a specific `method` and `path` to filter the telemetry data.

## Gotchas

- **Drill-down UI dependency** — Per commit `6fe57db`, this API is the backend for the "drill-down drawer" on the Health response-times table. Changes to the return shape of `responseTimes` will break the visibility of the detail view in the admin dashboard.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` (admin-level permissions implied).
- **Side effects**: Directly powers the `HealthPage` (via `page.tsx:73`) for displaying system performance metrics.

## External consumers

- None known.

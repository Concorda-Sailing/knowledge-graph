---
node_id: GET::/api/admin/response-times/requests
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 69b3544b97bc3b1d5864029f013dc955cc482006d2c736a9bd8e8bcf3f52c9d1
status: current
---

# GET /api/admin/response-times/requests

## Purpose

Provides granular drill-down data for investigating API latency and error rates. It returns individual request rows from the `activity_log` filtered by a specific HTTP method and resource path over a rolling window of hours. This is used by administrators to identify whether specific endpoints are experiencing outliers or high error rates, rather than just viewing aggregated statistics.

## Invariants

- **HTTP Method**: `GET`
- **Auth**: Requires a valid session via `require_auth` and must pass the `_require_system_admin` check.
- **Path Constraint**: The `path` query parameter has a maximum length of 500 characters.
- **Return Shape**: Returns a list of `ResponseTimeRequest` objects containing `created` (ISO string), `duration_ms`, `status_code`, `person_uuid`, and `ip_address`.
- **Ordering**: Results are strictly ordered by `duration_ms DESC` to highlight outliers.

## Gotchas

- **Drill-down intent**: This endpoint was specifically added to provide "drill-down endpoints for response-time investigations" (per commit `0313afa`). Use this when aggregated metrics are insufficient to identify specific failing requests.
- **Database load**: Because this performs a raw SQL query against the `activity_log` with variable `LIMIT` and `hours` parameters, high-frequency polling by an admin dashboard could impact DB performance.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_require_system_admin`.
- **Audit**: Reads from `activity_log`.
- **Side effects**: Data is consumed by the `adminHealthApi.responseTimesRequests` in the web dashboard to render latency graphs and error lists.

## External consumers

- concorda-web (admin dashboard)

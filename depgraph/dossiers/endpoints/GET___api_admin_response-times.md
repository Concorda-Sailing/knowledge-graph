---
node_id: GET::/api/admin/response-times
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a665c98323b23bddfa317f655579c12539052c932007b8177a3ec4aa39274b68
status: llm_drafted
---

# GET /api/admin/response-times

## Purpose

Provides observability into API latency by calculating percentiles (P50, P95, P99) and error rates per method and path. It is a diagnostic tool for administrators to identify slow or failing endpoints. It uses a custom NTILE-based approach to approximate percentiles because the underlying SQLite engine lacks native `percentile_cont` support.

## Invariants

- **Method/Path grouping**: Results are grouped by `action` (method) and `resource_type` (path).
- **Time window**: The `hours` parameter must be between 1 and 168 (inclusive).
- **Minimum sample size**: The `min_count` parameter filters out paths with insufficient data to ensure statistical relevance.
- **Return shape**: Returns a list of `ResponseTimeRow` objects containing `method`, `path`, `count`, `p50_ms`, `p95_ms`, `p99_ms`, `max_ms`, and `error_rate`.
- **Null safety**: If `duration_ms` or `status_code` are missing/null, the function defaults to `0` or `0.0` to prevent serialization errors.

## Gotchas

- **SQLite Limitation**: Because SQLite lacks native percentile functions, this relies on a complex `ROW_NUMBER()` window function. Any change to the SQL logic must account for the fact that we are approximating via NTILE-style boundary selection.
- **Data Gaps**: Rows where `duration_ms` was not recorded (due to pre-migration data or middleware skips) are explicitly excluded from the calculation.
- **Performance/Timeout**: The query relies on an index on `activity_log.created` and a `busy_timeout=10000` to remain performant under heavy load.

## Cross-cutting concerns

- **Auth**: Requires `_require_system_admin` via `current_user`.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.

## Open questions

- Should the `LIMIT 200` be moved to a query parameter to allow admins to see more/fewer high-latency paths?

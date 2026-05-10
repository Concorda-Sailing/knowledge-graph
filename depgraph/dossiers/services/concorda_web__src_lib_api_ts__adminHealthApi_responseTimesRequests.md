---
node_id: concorda-web::src/lib/api.ts::adminHealthApi.responseTimesRequests
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 19dfc9c14ec19515632520d95349fe42ba23843bb99a16453e122ce6f15346c9
status: llm_drafted
---

# adminHealthApi.responseTimesRequests

## Purpose

Fetches granular telemetry regarding API performance, specifically targeting request latency and error rates. It provides two distinct views: `responseTimesRequests` for high-level time-series bucketing (latency over time) and a more granular request-level view (individual request traces). Use this when building administrative health dashboards or drill-down views to diagnose system-wide performance degradation.

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid session/bearer token to access the `/api/admin/` namespace.
- **Returns `ResponseTimeRequest[]`** — the data is a collection of individual request objects used for drill-down analysis.
- **Query parameters are stringified** — `hours`, `min_duration_ms`, and `limit` are converted to strings via `URLSearchParams` before the fetch.
- **`only_errors` is a boolean flag** — if provided, it is appended to the query string as the literal string `"true"`.

## Gotchas

- **Drill-down dependency** — this method is the primary data source for the `ResponseTimeDrilldown` component. Changes to the return shape or parameter handling will break the admin health UI.
- **Complexity of `min_duration_ms`** — the parameter is optional and must be checked against `null` (not just falsy) to ensure `0` is a valid input for filtering extremely fast requests.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Directly populates the `ResponseTimeDrilldown` component in the admin health dashboard.

## External consumers

- N/A — internal to concorda-web.

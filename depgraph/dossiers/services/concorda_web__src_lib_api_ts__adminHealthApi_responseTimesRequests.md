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
Fetches detailed request-level data for administrative health monitoring. This function is distinct from `responseTimesRequests` (the sibling function in `adminHealthApi`), which provides aggregated time-series buckets rather than individual request logs. A future agent should reach for this specific function when building drill-down views or debugging specific latency spikes for a given API path or method.

## Invariants
* Uses `GET` via `fetchApiAuthenticated` to the `/api/admin/response-times/requests` endpoint.
* Requires authentication via the standard admin session.
* Returns a promise resolving to an array of `ResponseTimeRequest` objects.
* Parameters (`method`, `path`, `min_duration_ms`, `only_errors`, `limit`) are passed as URL search parameters.

## Gotchas
* **Parameter Type Casting**: The `only_errors` boolean is explicitly converted to the string `"true"` in the URL, while other numeric parameters like `limit` and `min_duration_ms` are cast via `String()`.
* **Nullability**: The `min_duration_ms` parameter is only appended to the request if it is not null, preventing `?min_duration_ms=null` from being sent to the server.

## Cross-cutting concerns
* **Auth**: Requires administrative privileges as it uses `fetchApiAuthenticated`.
* **Observability**: This is a consumer of the health monitoring data used by the admin dashboard to surface system performance.

## External consumers
* `concorda-web::src/components/admin/response-time-drilldown.tsx` (ResponseTimeDrilldown component).

## Open questions
* None.

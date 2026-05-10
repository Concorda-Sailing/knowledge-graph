---
node_id: concorda-web::src/lib/api.ts::adminHealthApi.responseTimesTimeseries
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 69a01ce64662bb78485b480a6122d58075632c4ca9ae1186ab2deabffef53711
status: llm_drafted
---

# adminHealthApi.responseTimesTimeseries

## Purpose

Fetches aggregated response-time telemetry for the system's health monitoring. It provides time-series data for specific API paths and methods, allowing the admin dashboard to visualize latency trends. Use this when you need to render the drill-down views for the Health page, rather than the raw `responseTimes` list.

## Invariants

- **Requires `fetchApiAuthenticated`** — All calls are authenticated and target `/api/admin/response-times/timeseries`.
- **Input parameters are mandatory** — `method` and `path` must be provided to filter the telemetry.
- **Returns `ResponseTimeBucket[]`** — The output is an array of time-bucketed latency data points.
- **Optional parameters are numeric strings** — `hours` and `bucket_minutes` are cast to strings via `URLSearchParams`.

## Gotchas

- **Drill-down dependency** — This method is the primary data source for the `ResponseTimeDrilldown` component. Any change to the return shape or parameter signature will break the admin health view.
- **Recent UI integration** — Per commit `6fe57db`, this method is used to drive the "drill-down drawer" on the Health page. Ensure any changes to the `ResponseTimeBucket` interface are compatible with the drawer's rendering logic.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level session).
- **Side effects**: Data is consumed by the `ResponseTimeDrilldown` component in the admin health dashboard.

## External consumers

None known.

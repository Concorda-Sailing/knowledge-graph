---
node_id: concorda-web::src/components/admin/response-time-drilldown.tsx::bucketSizeForHours
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c965d5aa3675773bb5a353bc14cb98b7090e889c88b73f932aad8689d94b924c
status: current
---

# bucketSizeForHours

## Purpose

Calculates the optimal number of buckets (granularity) for the response-time time-series chart based on the requested time window. It ensures the chart maintains a readable density (roughly 30-60 bars) so the visual shape of the latency spikes is visible without the UI becoming a "wall of pixels."

## Invariants

- **Input is `hours` (number)**: The function expects the total duration of the lookback window.
- **Output is `bucket_minutes`**: The returned value is used as the `bucket_minutes` argument for the `adminHealthApi.responseTimesTimeseries` call.
- **Non-linear scaling**: The bucket size increases as the window grows (2, 10, 30, or 60) to prevent over-granularity in long-range views.

## Gotchas

- **Backend datetime normalization**: Per commit `f444b4c4`, the UI must handle the fact that the API returns plain SQL datetime strings without the `Z` suffix. While `bucketSizeForHours` is a pure math helper, any logic consuming these buckets must ensure the `iso` string is normalized (via `formatRequestTime`) to prevent timezone drift.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Directly controls the density of the `adminHealthApi.responseTimesTimeseries` request; changing the logic here affects the visual density of the Health response-times table drill-down.

## External consumers

None known.

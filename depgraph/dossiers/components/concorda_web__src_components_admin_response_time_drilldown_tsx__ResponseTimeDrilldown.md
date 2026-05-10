---
node_id: concorda-web::src/components/admin/response-time-drilldown.tsx::ResponseTimeDrilldown
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 194a0de3d4b5d75834a18056b94949009e4b075bb94b12f45a02e4f3f4051f80
status: current
---

# ResponseTimeDrilldown

## Purpose

Provides a detailed drill-down view (typically in a drawer or modal) for API response time metrics. It fetches both time-series bucket data and a granular list of recent requests based on a specific API endpoint `selection`. Use this component when an admin needs to investigate whether latency spikes are caused by specific request patterns or high error rates.

## Invariants

- **Requires a `selection` object** containing `method`, `path`, and `hours` to initiate any API calls.
- **Fetches two distinct datasets**: `adminHealthApi.responseTimesTimeseries` for the visual chart and `adminHealthApi.responseTimesRequests` for the granular list.
- **`bucketSizeForHours` determines the granularity** of the time-series data to ensure the chart scale matches the requested time window.
- **`onlyErrors` toggle is independent**; toggling it triggers a refetch of the request list but does not re-fetch the time-series buckets.

## Gotchas

- **Timezone-aware rendering is mandatory.** Per commit `f444b4c`, all backend datetimes rendered within this component must be converted to the organization's timezone via `useConstants()` to avoid displaying browser-local times that mislead admins during incident investigation.
- **Race conditions in async effects.** The component uses a `cancelled` flag pattern in `useEffect` to prevent state updates on unmounted components or stale `selection` changes; do not remove these guards when adding new fetch logic.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session to access `adminHealthApi` endpoints.
- **Side effects**: Displays data derived from the Health response-times table.

## External consumers

None known.

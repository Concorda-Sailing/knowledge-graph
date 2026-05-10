---
node_id: concorda-web::src/app/members/admin/health/page.tsx::HealthPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 59f489507006c188272603b7c54452fe55f1202e8622f37f5e0f75ec606c1927
status: llm_drafted
---

# HealthPage

## Purpose

The administrative health dashboard for monitoring database and API performance. It provides real-time visibility into the database connection pool (checked-out vs. capacity) and endpoint response-time percentiles. It is used by administrators to diagnose latency spikes or connection exhaustion.

## Invariants

- **Database pool stats refresh every `POOL_REFRESH_MS`** (10 seconds) via `setInterval`.
- **Response time data is time-windowed** via the `hours` state; changing the hours triggers a new fetch.
- **`capacity` calculation** is a derived value: `pool.pool_size + pool.max_overflow`.
- **`latencyBadgeVariant` thresholds**: "secondary" at 500ms, "destructive" at 2000ms.

## Gotchas

- **Drill-down implementation**: Per commit `6fe57db`, the page includes a drill-down drawer for the response-times table. Ensure any changes to the `ResponseTimeRow` data structure are reflected in the drawer UI to avoid broken drill-downs.
- **Manual refresh requirement**: While the DB pool auto-refreshes, the response time data (`loadRt`) only refreshes when the `hours` state changes or the component mounts.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission via `SettingsPage`.
- **Side effects**: Visualizes `adminHealthApi.dbStats()` and `adminHealthApi.responseTimes()`.

## External consumers

None known.

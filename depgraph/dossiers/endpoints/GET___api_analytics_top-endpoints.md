---
node_id: GET::/api/analytics/top-endpoints
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e6c779ba8f4bcc8768d266474c31d6783979188f09f31f8ebb6cbe3eddc0d368
status: llm_drafted
---

# GET /api/analytics/top-endpoints

## Purpose

Provides a ranked list of the most frequently accessed API endpoints within a specific time window. It aggregates data from the `ActivityLog` to identify high-traffic resources, helping administrators identify usage patterns or potential bottlenecks. This is a distinct analytical tool for high-level resource monitoring, separate from user-specific activity tracking.

## Invariants

- **Requires elevated permissions** — Access is restricted to users with `org_admin` or `system_admin` roles via `require_any_role`.
- **Returns a list of objects** — Each object contains an `endpoint` (string) and a `count` (integer).
- **Input parameters are optional** — `start` and `end` dates can be null; if not provided, the window is resolved via `_resolve_window`.
- **Limit is constrained** — The `limit` parameter must be between 1 and 50.

## Gotchas

- **Date windowing logic** — Per commit `cdf2594`, the analytics engine was updated to support specific date ranges; ensure any changes to the `start`/`end` logic respect the `_resolve_window` behavior to avoid empty result sets.
- **Dependency on `ActivityLog`** — This endpoint relies entirely on the successful ingestion of logs by the middleware; if logging is bypassed or fails, this endpoint will return empty or stale data.

## Cross-cutting concerns

- **Auth**: Requires `org_admin` or `system_admin` via `require_any_role`.
- **Audit**: Aggregates data from the `ActivityLog` table.
- **Side effects**: Data is used to populate the analytics dashboard views in `concorda-web`.

## External consumers

- `concorda-web::src/lib/api.ts::analyticsApi.topEndpoints`

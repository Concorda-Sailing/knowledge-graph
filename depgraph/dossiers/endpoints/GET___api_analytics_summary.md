---
node_id: GET::/api/analytics/summary
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f5fcb8e3fa86b2609d58ab9f2522828c689685584fb9fc01689376e659f87852
status: current
---

# GET /api/analytics/summary

## Purpose

Provides high-level usage metrics for the organization's dashboard. It aggregates data from `ActivityLog` and `AuthToken` to report on request volume, user/visitor counts, and active sessions. This is the primary data source for the administrative overview UI.

## Invariants

- **Requires elevated privileges** — Access is guarded by `require_any_role("org_admin", "system_admin")`.
- **Returns a JSON object** with keys: `start`, `end`, `total_requests`, `unique_users`, `unique_visitors`, and `active_sessions`.
- **Date windowing is handled by `_resolve_window`** — if `start` or `end` are omitted, it defaults to a 7-day window relative to `now`.
- **`active_sessions` is a point-in-time metric** — unlike other fields, it is not bounded by the `start`/`end` parameters; it counts all `AuthToken` entries where `expires_at > datetime.utcnow()`.

## Gotchas

- **Date range logic was recently updated** — per commit `cdf2594`, the analytics engine now supports specific date range parameters (previously likely hardcoded or limited to a fixed window).
- **`unique_visitors` relies on IP address** — the count is derived from `distinct(ActivityLog.ip_address)`. If a user rotates IPs or uses a VPN, they may be counted as a new visitor.
- **`unique_users` excludes nulls** — the query explicitly filters for `person_uuid.isnot(None)`, meaning unauthenticated/anonymous requests are not counted in the `unique_users` metric.

## Cross-cutting concerns

- **Auth**: Requires `org_admin` or `system_admin` via `require_any_role`.
- **Audit**: Reads from `ActivityLog`, which is populated by the activity logging middleware (see commit `7c1ad77`).
- **Side effects**: Data drives the administrative dashboard overview.

## External consumers

- `concorda-web` (via `analyticsApi.summary`)

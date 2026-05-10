---
node_id: GET::/api/analytics/online-now
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5bf4cd50872b71ee5fc2cdcefa1cd9a5d37a19a7cc4f46680c4ebc7e00d7e365
status: llm_drafted
---

# GET /api/analytics/online-now

## Purpose

Provides a real-time snapshot of active users within an organization. It identifies users who have had activity recorded in the `ActivityLog` within the last 15 minutes, returning their identity and the last resource type they accessed. This is used for high-level administrative monitoring of active sessions.

## Invariants

- **Requires elevated privileges** — Access is restricted via `require_any_role("org_admin", "system_admin")`.
- **Returns a list of user objects** — Each object contains `person_uuid`, `name`, `last_seen` (ISO timestamp), and `last_page` (resource type).
- **Uses a 15-minute sliding window** — The `cutoff` is calculated as `datetime.utcnow() - timedelta(minutes=15)`.
- **Handles missing person records** — If a `person_uuid` exists in logs but not in the `Person` table, the name defaults to `"Unknown"`.

## Gotchas

- **Dependency on `ActivityLog` middleware** — This endpoint relies on the recent addition of activity logging middleware (commit `7c1ad77`) to populate the `ActivityLog` table; without that middleware active, this endpoint will return an empty list even if users are active.
- **Performance at scale** — The function performs a `db.query(Person)` inside a loop for every user found in the results. While fine for small orgs, this is an $O(N)$ query pattern that could cause latency if many users are active simultaneously.

## Cross-cutting concerns

- **Auth**: Guarded by `require_any_role("org_admin", "system_admin")`.
- **Audit**: Relies on `ActivityLog` entries created by the activity logging middleware.
- **Side effects**: None.

## External consumers

- `concorda-web` (via `analyticsApi.onlineNow`).

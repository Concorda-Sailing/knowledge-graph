---
node_id: GET::/api/analytics/active-users
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6a79f6813565a7a066732d13e48d8efb82734a09cfc8f9f8c17528508506248b
status: llm_drafted
---

# GET /api/analytics/active-users

## Purpose

Returns a ranked list of the most active users within a specific time window, based on the count of entries in the `ActivityLog`. This endpoint is used to drive the "Active Users" section of the organization's analytics dashboard. It is distinct from `/api/daily-activity` (which provides time-series data for charting) by focusing on individual user engagement rather than daily volume trends.

## Invariants

- **HTTP Method**: `GET`.
- **Authentication**: Requires a user with either `org_admin` or `system_admin` roles via the `require_any_role` dependency.
- **Return Shape**: A list of objects containing `person_uuid` (string), `name` (string), and `count` (integer).
- **Query Parameters**: `start` and `end` are optional `date` objects; `limit` defaults to 20 and is constrained between 1 and 50.
- **Data Integrity**: If a `person_uuid` exists in the log but the corresponding `Person` record has been deleted or is missing, the `name` field defaults to `"Unknown"`.

## Gotchas

- **Date Windowing**: The `_resolve_window` helper (used in the `since`/`until` calculation) defaults to a 7-day window if no parameters are provided.
- **Role Dependency**: Access is strictly guarded by `require_any_role("org_admin", "system_admin")`. Attempting to call this with a standard user role will result in a 403/401 error.

## Cross-cutting concerns

- **Auth**: Requires `org_admin` or `system_admin` roles.
- **Side effects**: Data is derived from the `ActivityLog` table; changes to user activity or person records directly impact the counts and names displayed here.

## External consumers

- `concorda-web` (via `analyticsApi.activeUsers`).

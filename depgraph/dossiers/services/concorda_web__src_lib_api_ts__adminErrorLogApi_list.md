---
node_id: concorda-web::src/lib/api.ts::adminErrorLogApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3f0d0b1dac55e92c3d900acd471dc1418afdbece5b5d0a889ac4797c8226f839
status: llm_drafted
---

# adminErrorLogApi.list

## Purpose

Fetches a list of system error logs for administrative oversight. It provides a filtered view of error events, allowing admins to drill down into specific issues via `status_code` or `fingerprint`. Use this method when building views that require high-level error monitoring or when navigating from the `ErrorLogPage` to specific error details.

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid session token to access the `/api/admin/` namespace.
- **Returns an array of `ErrorLogRow`** — the base shape includes `fingerprint` and `notified_at`.
- **Supports optional filtering** — `limit`, `status_code`, and `fingerprint` are the only valid query parameters.
- **Endpoint path is static** — `/api/admin/error-log`.

## Gotchas

- **Drill-down UI dependency** — The `ErrorLogPage` (page.tsx:49) relies on this list to drive the navigation to detailed error views. Changes to the return shape of `list` may break the drill-down drawer functionality.
- **Admin-only access** — Because it uses `fetchApiAuthenticated`, this method will fail if the user lacks the necessary administrative permissions, even if they are a valid authenticated user.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges via `fetchApiAuthenticated`.
- **Side effects**: Used by the `ErrorLogPage` to populate the administrative error monitoring dashboard.

## External consumers

None known.

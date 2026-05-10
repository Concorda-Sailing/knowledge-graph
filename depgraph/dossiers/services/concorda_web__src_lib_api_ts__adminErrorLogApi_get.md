---
node_id: concorda-web::src/lib/api.ts::adminErrorLogApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1b6ae34a8c90d45c54d18520d51bf8502f0da7e6a28d3c77d40c7cca81faee91
status: llm_drafted
---

# adminErrorLogApi.get

## Purpose

Fetches detailed error information for a specific error log entry. It is a specialized administrative endpoint used to drill down into a single error event, providing the context necessary for debugging system-level issues. It is distinct from `adminErrorLogApi.list` (or the implicit list method), which returns collections of `ErrorLogRow` objects.

## Invariants

- **Requires a valid `id` string** to construct the path `/api/admin/error-log/{id}`.
- **Uses `fetchApiAuthenticated`** — the caller must have an active, authenticated session with administrative privileges.
- **Returns an `ErrorLogDetail` object** — this object contains the full context of the error, not just the summary fields found in the list view.

## Gotchas

- **Admin-only access** — because this uses `fetchApiAuthenticated`, it relies on the backend's ability to verify the user's admin role.
- **UI Drill-down dependency** — per commit `6fe57db`, this endpoint supports the "drill-down drawer" on the Health response-times table, allowing admins to move from a high-level view to specific error details.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Populates the detail view for the admin drill-down drawer.

## External consumers

- `concorda-web::src/app/members/admin/errors/page.tsx::ErrorLogPage` (via `hook_call`)

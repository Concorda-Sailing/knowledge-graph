---
node_id: concorda-web::src/lib/api.ts::adminApi.stats
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 30a571d44750718f5db72f69af52c6d969a9d5324ebfb34921f32b3b8b813255
status: current
---

# adminApi.stats

## Purpose

Provides access to high-level administrative metrics and system health data. It is a specialized endpoint for retrieving the `Stats` object, which is used to drive administrative overview pages. Use this when you need a snapshot of system-wide metrics rather than specific user or member data.

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to be present in the request context.
- **Returns a `Stats` object** — the return type is a single object representing system-wide metrics.
- **No parameters accepted** — unlike `members` which accepts search/pagination, `stats` is a parameterless call to `/api/admin/stats`.

## Gotchas

- **Directly drives the Health page** — per commit `37794d5`, this endpoint (and the broader admin API) is responsible for surfacing the "Health page" which displays pool stats and response times.
- **Dependency on `fetchApiAuthenticated`** — if the authentication wrapper is modified, this method will fail as it relies on the injected credentials for the `/api/admin/stats` path.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: Data returned here is used to populate the "Health page" metrics.

## External consumers

- `AdminMembershipsPage` in `concorda-web/src/app/members/admin/memberships/page.tsx`.

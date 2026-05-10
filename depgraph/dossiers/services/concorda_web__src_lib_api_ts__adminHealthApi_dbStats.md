---
node_id: concorda-web::src/lib/api.ts::adminHealthApi.dbStats
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 39aa972de63e6313e4b0354fc697c4cfca9a58f05876e812d912512caa372d29
status: current
---

# adminHealthApi.dbStats

## Purpose

Provides a single endpoint to retrieve database pool statistics. It is used to monitor the health and connectivity of the underlying database-driven services. This method is distinct from the `responseTimes` methods in the same object, which focus on API latency and request patterns rather than database connection state.

## Invariants

- **Uses `fetchApiAuthenticated`** — Requires a valid authenticated session to access the `/api/admin/db-stats` endpoint.
- **Returns `DbPoolStats`** — The return type is a specific shape representing the current state of the database connection pool.

## Gotchas

- **Directly supports the Health page** — Per commit `37794d5`, this method was added to surface pool stats on the admin Health page. Any changes to the return shape will break the `HealthPage` component.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level credentials).
- **Side effects**: Used by the `HealthPage` to display real-time system status.

## External consumers

None known.

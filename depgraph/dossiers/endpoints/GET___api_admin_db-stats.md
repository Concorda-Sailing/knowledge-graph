---
node_id: GET::/api/admin/db-stats
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 559bfbda4c9489e10842653e99adcda82212a525d51d3015f2508dada6ced83f
status: llm_drafted
---

# GET /api/admin/db-stats

## Purpose

Provides real-time visibility into the SQLAlchemy connection pool and the underlying SQLite state. It is used by administrators to diagnose connection exhaustion and monitor the health of the database engine, specifically tracking the status of the WAL (Write-Ahead Log) and busy timeouts.

## Invariants

- **Requires `_require_system_admin`** — The request must pass `require_auth` and satisfy the system admin role check.
- **Returns `DbPoolStats`** — The response shape includes `pool_class`, `pool_size`, `max_overflow`, `checked_out`, `checked_in`, `overflow`, `journal_mode`, `wal_size_bytes`, and `busy_timeout_ms`.
- **`wal_size_bytes` is nullable** — If the `-wal` file is not present or inaccessible, this returns `None` (or `null` in JSON) rather than failing.

## Gotchas

- **Connection-pool exhaustion risk** — Per the docstring, a rising `checked_out` count relative to `pool_size + max_overflow` indicates sessions are being held open across slow I/O operations.
- **Recent fix for exhaustion** — See commit `8b2e30a` (`fix(api): resolve connection-pool exhaustion + add observability`), which addressed issues where unreleased sessions were impacting API availability.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with system admin privileges via `_require_system_admin`.
- **Side effects**: Used by `adminHealthApi.dbStats` in `concorda-web` to drive the admin health dashboard.

## External consumers

- `concorda-web::src/lib/api.ts::adminHealthApi.dbStats`

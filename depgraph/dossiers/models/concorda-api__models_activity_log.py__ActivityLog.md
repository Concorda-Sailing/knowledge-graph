---
node_id: concorda-api::models/activity_log.py::ActivityLog
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 36dc7ec70f8284267880cc7d6fc71a6d28be6070654063d253d04d57d9fda4ac
status: llm_drafted
---

# ActivityLog

## Purpose

Append-only audit/observability log for every notable user action in the API: logins, registrations, page views, file uploads, crewfinder contacts, event registrations, profile updates, and sensitive admin mutations (role grants, etc.). Single denormalized table — `(person_uuid, action, resource_type, resource_uuid, detail, status_code, duration_ms, ip_address, user_agent)` plus `BaseModel`'s `uuid`/`created_at`. Written by the activity-logging middleware on every request; read exclusively by the `/api/analytics/*` endpoints for active-user counts, daily-activity rollups, presence ("online now"), summary cards, and top-endpoint tables. Treat it as both compliance trail and product telemetry.

## Invariants

- Append-only. No update or delete paths exist; analytics queries assume rows are immutable and timestamps come from `created_at`.
- `action` is required; everything else (including `person_uuid`) is nullable — anonymous traffic and pre-auth requests log too.
- `action`, `status_code`, `duration_ms`, and `person_uuid` are indexed; analytics filters and `GROUP BY`s rely on these. Removing an index will regress dashboard latency.
- `action` is a free-form `String(50)` — the docstring enumerates the in-use vocabulary but there is no DB-level enum. New action names ship by writing them at the call site.
- `detail` capped at 500 chars and `user_agent` at 500; the middleware must truncate, not raise.
- `ip_address` is `String(45)` to fit IPv6.
- `type="ActivityLog"` is forced in `__init__` for `BaseModel`'s single-table-inheritance discriminator — do not override.

## Gotchas

- This table grows fast — every request writes a row. Commit `8b2e30a` ("resolve connection-pool exhaustion + add observability") landed alongside the analytics rollout because the volume surfaced pool-exhaustion bugs; any change that adds a synchronous write or a per-request read here will reproduce that incident. Keep writes fire-and-forget where the middleware allows.
- No FK on `person_uuid` or `resource_uuid` — they are bare `String(36)`. Rows survive person/resource deletion, which is the point for an audit log but means analytics joins must be left-outer and tolerate dangling UUIDs.
- `action` values are stringly-typed. A typo at the call site silently creates a new bucket in the analytics dashboards; there is no validation.
- `resource_type` is `String(30)` — longer model names (anything past "organization") will truncate.
- No retention/TTL policy in the model or migrations. Table will grow unbounded.

## Cross-cutting concerns

- **Audit**: this *is* the audit surface. Admin role grants, sensitive mutations, and auth events all land here; deleting or rewriting rows breaks compliance posture.
- **Auth/PII**: stores `ip_address` and `user_agent` against `person_uuid`. Treat as PII for export/erasure requests — there is currently no scrubbing path.
- **Write path**: populated by activity-logging middleware (see commit `7c1ad77`), not by individual routers. Adding a new logged action means emitting from middleware or a service, not adding a column.
- **Read path**: only `routers/analytics.py` (5 endpoints). Those endpoints are the consumer surface — schema changes must keep their `db_query` calls compiling.
- **Rate limits**: in-memory rate limiter in `auth.py` is a separate concern, but note the table also captures auth failures, so it is the durable record when the limiter resets.

## External consumers

None known. No webhooks, no scheduled exports, no third-party sinks. All five dependents are first-party analytics routes.

## Open questions

- Retention: at current write rate, when does this need partitioning/archival? No policy is encoded.
- Should `action` become an enum (DB or app-level) before the vocabulary drifts further?
- Is `detail`'s 500-char cap enough for the admin-mutation use case (role grants with reasoning), or do we need a separate richer audit table for Tier-C-style events?

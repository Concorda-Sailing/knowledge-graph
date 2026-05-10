---
node_id: GET::/api/admin/error-log
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 612c24f0d4e55f44ff0fe9d57b210f8890741a3e56ab809f0ca0a8cb3dd0c09b
status: current
---

# GET /api/admin/error-log

## Purpose

Provides administrative access to the system's error logs. It allows administrators to list recent errors with optional filtering by `status_code` or `fingerprint`, or to retrieve the full details of a specific error via its ID. This is the primary interface for debugging production exceptions and monitoring the health of the error-alert pipeline.

## Invariants

- **Requires `admin.audit.view` permission** via the `require_permission` dependency.
- **Returns a list of `ErrorLogRow` objects** for the collection endpoint, or a single `ErrorLogDetail` (including the `traceback` string) for the ID-specific endpoint.
- **Supports pagination via `limit`**, which accepts an integer between 1 and 500.
- **Orders by recency** — the list endpoint always returns results ordered by `ErrorLog.created.desc()`.

## Gotchas

- **Strict permission requirement**: Access is gated by `require_permission("admin.audit.view")`. If a user has general admin rights but lacks this specific permission, they will receive a 403.
- **Traceback availability**: The `traceback` field is only present in the `ErrorLogDetail` model, not the base `ErrorLogRow` used in the list endpoint.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Part of the "error-alert pipeline" introduced in commit `da1589d`.

## External consumers

None known.

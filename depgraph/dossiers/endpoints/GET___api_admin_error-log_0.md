---
node_id: GET::/api/admin/error-log/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c5b442644f95529b1c8c77fc26fe0413afb5166a8bd560486d29575b66b88f8
status: llm_drafted
---

# GET /api/admin/error-log/{error_id}

## Purpose

Fetches a single error log entry by its unique identifier. This is a high-privilege endpoint used to inspect specific stack traces and error metadata for debugging purposes. It is distinct from the collection-based filtering endpoint (which allows filtering by `status_code` or `fingerprint`) by providing the full `ErrorLogDetail` for a specific instance.

## Invariants

- **Requires `admin.audit.view` permission** — Access is guarded by the `require_permission` dependency.
- **Returns `ErrorLogDetail`** — The response shape is strictly defined by the `ErrorLogDetail` model.
- **Returns 404 if not found** — If the `error_id` does not match an existing record, the function explicitly raises an `HTTPException` with a 404 status.
- **Strictly single-row lookup** — Uses `.first()` on the query; it is designed to retrieve exactly one record or fail.

## Gotchas

- **Permission dependency** — Access is gated by `require_permission("admin.audit.view")`. If a user has general admin access but lacks this specific audit permission, this call will fail.
- **Recent policy changes** — Per commit `da1589d` (`feat: versioned policies, error-alert pipeline...`), this endpoint is part of the new structured error-alert pipeline. Ensure any changes to the error-logging logic respect the versioned policy structures introduced in that commit.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission via `require_permission`.
- **Audit**: Y (This endpoint is the retrieval side of the error-alert pipeline).

## External consumers

- `concorda-web::src/lib/api.ts::adminErrorLogApi.get` (used for displaying detailed error views in the admin dashboard).

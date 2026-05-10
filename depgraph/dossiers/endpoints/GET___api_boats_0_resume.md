---
node_id: GET::/api/boats/{0}/resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1298d4ecd319304f411fe1abaae1b19aff73d917bce6318eaf2bd2311cc3890d
status: current
---

# GET /api/boats/{boat_id}/resume

## Purpose

Retrieves the `BoatResume` object for a specific boat. This endpoint provides high-level metadata (manufacturer, class, dimensions, and media URLs) intended for display in overview components. It is distinct from the `punchlist` endpoints which handle operational tasks; this is a read-only view of the boat's identity and physical characteristics.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Strict membership check**: Access is restricted to users with an `active` or `invited` status in the boat's crew.
- **Returns a single `BoatResume` object** or a `404 Not Found` if the resume record does not exist for the given `boat_id`.
- **Returns a `403 Forbidden`** if the user is authenticated but does not meet the specific membership status requirements.

## Gotchas

- **Status-based access control**: Unlike the punchlist endpoints which use `_require_crew_or_owner`, this endpoint specifically checks `membership.status` against a hardcoded tuple `("active", "invited")`. If a user is in a "pending" or "revoked" state, they will receive a 403 even if they are technically in the database for that boat.
- **Dependency on `_get_boat_or_404`**: The function first validates the existence of the boat via `_get_boat_or_404` before checking membership, ensuring a 404 is returned for invalid IDs before any auth-related 403s are evaluated.

## Cross-cutting concerns

- **Auth**: Uses `current_user: AuthUser = Depends(require_auth)` and validates membership status via `_get_crew_membership`.
- **Side effects**: None. This is a read-only GET endpoint.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.getResume`

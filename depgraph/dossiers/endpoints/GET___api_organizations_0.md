---
node_id: GET::/api/organizations/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c65ef9a7480abf90d3f8d57cfa962f9623d8b8a2b8fd275253bd881311af6d34
status: llm_drafted
---

# GET /api/organizations/{org_id}

## Purpose

Fetches the full profile of a specific organization by its unique identifier. This is the primary read-only endpoint for retrieving organization metadata, used by both administrative and general-purpose views. It is distinct from the `POST` and `PUT` endpoints in this module, which require higher privilege levels to modify the organization state.

## Invariants

- **HTTP Method is `GET`**.
- **Requires `org_id`** as a path parameter.
- **Returns `OrganizationRead` schema**. The response includes all core organization identity and configuration fields.
- **Returns 404 on missing ID**. If the `org_id` does not match an existing record, the API raises an `HTTPException` with the detail `"Organization not found"`.

## Gotchas

- **No authentication required for retrieval.** Unlike the `POST`, `PUT`, and `DELETE` methods in this file which depend on `_require_admin`, this `GET` endpoint is public/unauthenticated.
- **Recent security hardening.** Per commit `c9a7c41` ("security: tier-A IDOR audit fixes"), ensure that while this endpoint is public, any subsequent logic in the frontend that uses this data respects the tier-based scoping established in the organization router.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `organizationsApi.get` in `concorda-web` to populate organization-level context and settings.

## External consumers

- `concorda-web::src/lib/api.ts` (via `organizationsApi.get`).

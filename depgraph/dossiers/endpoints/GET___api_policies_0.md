---
node_id: GET::/api/policies/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 196d59f9f0abdf9ce795b0c6693d6f6c4965b618c55eb95a0d11b572d6938edb
status: llm_drafted
---

# GET /api/policies/{slug}

## Purpose

Retrieves the currently active version of a specific policy via its slug. This endpoint is used to fetch the most recent, published contract details (body, effective date, etc.) before a user is prompted to accept them. It is distinct from the `/me/pending` endpoint, which is used to fetch a list of specific contracts awaiting user action.

## Invariants

- **Method is `GET`** with a path parameter `{slug}`.
- **Returns `PolicyDetail`** containing `id`, `slug`, `name`, `version`, `body`, `effective_date`, and `is_material_change`.
- **Throws 404** if no active version exists for the provided slug.
- **Requires valid slug** via `_validate_slug(slug)` before execution.

## Gotchas

- **Strict versioning requirement**: Per commit `da1589d` (feat: versioned policies), this endpoint only returns the "active" version. If a policy exists but has not been published/activated, the API returns a 404.
- **Slug validation**: The `_validate_slug` check is a prerequisite; passing an invalid slug format will fail before the database lookup occurs.

## Cross-cutting concerns

- **Auth**: None (publicly accessible via slug for pre-authentication viewing).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: None.

## External consumers

- `concorda-web` (via `policiesApi.get`)

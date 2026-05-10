---
node_id: GET::/api/policies/admin/{0}/versions
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 890201f1c34fc966bc3dd6e9c48f93e55f4eef50306a045462084819f312f624
status: llm_drafted
---

# GET /api/policies/admin/{slug}/versions

## Purpose

Retrieves the version history for a specific policy (Contract) identified by its slug. It returns a list of `PolicyVersion` objects, including metadata like the version string, effective date, and the current `acceptance_count` (how many users have accepted this specific version). This is used by the admin dashboard to audit historical changes and track user compliance.

## Invariants

- **Method is `GET`** and requires the `slug` path parameter.
- **Auth requirement** is the `admin.policies.view` permission.
- **Returns a list of `PolicyVersion` objects**, ordered by `Contract.created` in descending order (newest first).
- **`acceptance_count` is calculated dynamically** via a join with `PersonContractAcceptance` to ensure the count reflects the current state of the database.
- **Returns an empty list `[]`** if no contract matches the provided slug, rather than a 404.

## Gotchas

- **`_validate_slug(slug)` is a mandatory guard.** If the slug is malformed or does not exist in the registry, the endpoint will fail before attempting the query.
- **Version collision prevention:** While this is a `GET` endpoint, it is tightly coupled with the `POST` behavior in the same router. Per the logic in the sibling `publish_version` method, attempting to create a version that already exists will trigger a `409 Conflict`.

## Cross-cutting concerns

- **Auth**: Requires `admin.policies.view` permission via `require_permission`.
- **Audit**: Indirectly supports audit trails by providing the historical `created` and `modified` timestamps for policy changes.
- **Side effects**: Used by the admin UI to populate the policy version history table.

## External consumers

- `concorda-web` (via `adminPoliciesApi.listVersions`)

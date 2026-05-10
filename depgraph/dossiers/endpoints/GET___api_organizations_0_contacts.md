---
node_id: GET::/api/organizations/{0}/contacts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1b92a7c8d46b13b5b85a6a85f0bbe0a38fb7caf7c185c7c875345af1b8474e12
status: llm_drafted
---

# GET /api/organizations/{org_id}/contacts

## Purpose

Retrieves a list of all contacts associated with a specific organization, including their assigned roles and contact details. This endpoint is used to populate directory views and administrative contact lists. It is distinct from the `POST` method in the same router, which creates the contact-role relationship, whereas this is a read-only view of existing associations.

## Invariants

- **HTTP Method is GET.**
- **Requires `_require_admin` dependency.** Access is restricted to users with administrative privileges.
- **Returns a list of `ContactWithRole` objects.** Each object contains `id`, `name`, `email`, `phone`, `role`, and `contact_role_id`.
- **Filters by `entity_type == "organization"`.** The query specifically looks for roles where the entity type is explicitly set to organization.

## Gotchas

- **Strict Admin Requirement.** Per commit `058aa8c` (security: tier-C cross-org scope enforcement), this endpoint is protected by `_require_admin`. Any attempt to access this via a non-admin token will fail, ensuring tier-C cross-org scope enforcement is maintained.
- **Role-Contact Coupling.** The endpoint relies on a join-like logic between `ContactRole` and `Contact`. If a `ContactRole` exists but the underlying `Contact` record is missing or deleted, that entry is silently skipped in the loop (see `if contact:` guard).

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `concorda-web::src/lib/api.ts::orgContactsApi.list`

## Open questions

- Should the endpoint support pagination? Currently, it returns all contacts for an organization in a single list, which may cause latency issues for very large organizations.

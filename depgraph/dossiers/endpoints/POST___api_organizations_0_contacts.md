---
node_id: POST::/api/organizations/{0}/contacts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4d679892d1ba95a066408a0680bc7932b41f3efdf744b84969590c5fdc69aba6
status: current
---

# POST /api/organizations/{org_id}/contacts

## Purpose

Creates a new contact record and simultaneously assigns them a specific role within the organization. This is a composite operation: it instantiates a `Contact` (storing name, email, and phone) and a `ContactRole` (linking the contact to the `org_id` with a specific role string). Use this endpoint when adding a person to an organization's directory, rather than just creating a standalone contact.

## Invariants

- **HTTP Method**: `POST`
- **Path**: `/{org_id}/contacts`
- **Auth Requirement**: Requires a user with `_require_admin` privileges.
- **Scope Requirement**: Must pass `_require_org_admin_scope(org_id, current_user)` to ensure the user has administrative rights over the specific organization.
- **Return Shape**: Returns a `ContactWithRole` object containing the `id`, `name`, `email`, `phone`, `role`, and `contact_role_id`.
- **Data Composition**: The `name` field is constructed by concatenating `first_name` and `last_name` from the input payload.

## Gotchas

- **Strict Scope Enforcement**: Per commit `058aa8c` (`security: tier-C cross-org scope enforcement`), this endpoint relies on strict organization-level boundary checks. A user might be an admin in one organization but cannot use this endpoint to add contacts to another without the correct `org_id` scope.
- **IDOR Protection**: Recent security hardening (commit `c9a7c41`) ensures that `_require_org_admin_scope` is strictly enforced to prevent cross-org contact injection.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` and passes `_require_org_admin_scope`.
- **Audit**: N/A
- **Rate limit**: None known.
- **Side effects**: Creates a new entry in the organization's contact directory.

## External consumers

- `concorda-web::src/lib/api.ts::orgContactsApi.create`

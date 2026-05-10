---
node_id: DELETE::/api/organizations/{0}/contacts/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bd414d4d4f07e9a1a59431ad435fa546967682c2e9eb630fcc91435f32a5f94d
status: current
---

# DELETE /api/organizations/{org_id}/contacts/{contact_role_id}

## Purpose

Removes a specific contact role assignment from an organization. It targets the `ContactRole` join entity rather than a user or a person, effectively severing the link between an organization and a contact. Use this endpoint when an admin needs to revoke access or remove a person's association with an organization without deleting the person themselves.

## Invariants

- **HTTP Method/Path**: `DELETE /api/organizations/{org_id}/contacts/{contact_role_id}`.
- **Auth Requirement**: Requires a user with `_require_admin` status.
- **Scope Enforcement**: Must pass `_require_org_admin_scope` to ensure the admin has authority over the specific `org_id`.
- **Return Shape**: Returns a `204 No Content` on success.
- **Error State**: Returns `404 Not Found` if the `contact_role_id` does not exist or is not associated with the provided `org_id`.

## Gotchas

- **Strict IDOR protection**: Per commit `058aa8c` (security: tier-C cross-org scope enforcement), this endpoint is strictly guarded. You cannot delete a contact role for an organization you do not explicitly have admin scope for, even if you are a global admin.
- **Two-part identifier requirement**: The `org_id` and `contact_role_id` must match. The query specifically filters by both `ContactRole.id == contact_role_id` AND `ContactRole.entity_uuid == org_id`. If the contact exists but belongs to a different organization, it will return a 404 rather than a 403.

## Cross-cutting concerns

- **Auth**: Uses `_require_admin` and `_require_org_admin_scope`.
- **Audit**: N/A.
- **Side effects**: Removing a contact role will immediately revoke that user's ability to access organization-specific administrative views or data-driven components (e.g., organization settings or member lists) that rely on this role assignment.

## External consumers

- `concorda-web::src/lib/api.ts::orgContactsApi.remove`

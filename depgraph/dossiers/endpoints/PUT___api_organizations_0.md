---
node_id: PUT::/api/organizations/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5edf0f33a0873f1550503afddb74d0fd7851612789492ce3f4b27cc5e68f3971
status: current
---

# PUT /api/organizations/{org_id}

## Purpose

Updates the metadata of an existing organization. It accepts an `OrganizationCreate` schema to perform a partial or full update on the organization's attributes. This is the primary method for administrative changes to organization names, settings, or configurations.

## Invariants

- **HTTP Method is `PUT`** — used for full/partial updates of the organization resource.
- **Requires `_require_admin`** — the caller must be authenticated as a global admin.
- **Requires `_require_org_admin_scope`** — even with admin credentials, the user must have specific scope permissions for the target `org_id`.
- **Returns `OrganizationRead`** — the response shape is the read-optimized version of the organization.
- **Atomic attribute updates** — the function iterates through the provided model fields and uses `setattr` to update the existing database object before committing.

## Gotchas

- **Tier-C/Tier-A Security Enforcement** — per commits `058aa8c` and `c9a7c41`, this endpoint is subject to strict cross-org scope enforcement. A user might have admin rights in one organization but will be blocked here if they attempt to update a different `org_id` without the correct scope.
- **Strict Admin Dependency** — unlike some other organization endpoints, this relies on both `_require_admin` and `_require_org_admin_scope`. If a developer attempts to use this for a "user-level" organization setting change, it will fail with a 403/401.

## Cross-cutting concerns

- **Auth**: Depends on `_require_admin` and `_require_org_admin_scope` for authorization.
- **Audit**: Y (Implicitly via the database commit on the `Organization` model).
- **Side effects**: Changes to organization metadata may affect any downstream services or UI components that rely on organization-specific settings (e.g., branding or localized settings).

## External consumers

- `concorda-web::src/lib/api.ts::organizationsApi.update`

---
node_id: POST::/api/organizations
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2486b34f1630753481c78d9516afe3321f2f3c063fb086364aa949039f7a1db8
status: current
---

# POST /api/organizations

## Purpose

Creates a new organization record in the database. This is the primary entry point for establishing a new organizational entity within the system. It is distinct from the `PUT` endpoint, which is used for updating existing organization metadata.

## Invariants

- **HTTP Method:** `POST`
- **Path:** `/api/organizations`
- **Auth Requirement:** Requires a valid session with `_require_admin` privileges.
- **Return Shape:** Returns the newly created `OrganizationRead` object, including the generated ID.
- **Data Model:** Expects an `OrganizationCreate` Pydantic model for the request body.

## Gotchas

- **Admin-only access:** Per commit `bb9dce0`, all organization-level endpoints (including this one) now require auth middleware to ensure only admins can create organizations.
- **Strict Scope Enforcement:** Recent security hardening (commits `058aa8c` and `c9a7c41`) ensures that organization creation and management are strictly gated by tier-C and tier-A scope checks to prevent IDOR vulnerabilities.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Audit**: N/A
- **Side effects**: Creating an organization is the prerequisite for establishing the organizational hierarchy used by the `crew finder` and `sailing center` features.

## External consumers

- `concorda-web::src/lib/api.ts::organizationsApi.create`

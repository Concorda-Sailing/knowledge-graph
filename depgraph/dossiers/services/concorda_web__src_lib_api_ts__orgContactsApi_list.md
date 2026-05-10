---
node_id: concorda-web::src/lib/api.ts::orgContactsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c6d571450094a979364e477814e3306d828a036cef735bf6f5f9786392fc4220
status: current
---

# orgContactsApi.list

## Purpose

Provides a programmatic interface for managing organization-specific contacts. This service handles the retrieval, creation, updating, and deletion of contact records (crew, owners, etc.) associated with a specific organization. Use this when you need to manage the people-side of an organization's membership or administrative roster, rather than the directory-wide person records.

## Invariants

- **Requires `orgId`** for every operation to scope the request to a specific organization.
- **Uses `fetchApiAuthenticated`** to ensure all requests include the necessary bearer token.
- **`list` returns an array of `OrgContact` objects**, which include a `contact_role_id`.
- **`create` requires a specific payload shape** including `first_name`, `last_name`, `email`, `phone`, and `role`.
- **`update` and `remove` target a specific `contactRoleId`** to modify or delete a specific entry within the organization.

## Gotchas

- **`create` and `update` require explicit name fields.** Unlike the `DirectoryPerson` model, this API expects `first_name` and `last_name` as distinct fields in the request body.
- **Role-based access control is critical.** Per commit `47688ac`, certain actions (like accepting co-owner invites) require specific membership types; ensure the `role` passed to `create` aligns with the intended organizational permissions.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires a valid session/token).
- **Side effects**: Changes to these contacts (via `create`, `update`, or `remove`) directly impact the visibility and availability of users in the `directoryApi.list` and the `crewfinderApi` search results.

## External consumers

- `ClubEditPage` in the members/admin dashboard.

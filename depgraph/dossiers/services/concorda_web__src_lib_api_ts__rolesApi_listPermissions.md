---
node_id: concorda-web::src/lib/api.ts::rolesApi.listPermissions
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae599e65f2c194ef97d5eea0f4016c46ff7c771258da5d9a9ca67c3380a82fe0
status: current
---

# rolesApi.listPermissions

## Purpose

Fetches the global list of all available permissions from the server. This is a read-only helper used to populate UI elements (like checkboxes or selection lists) that require a complete set of valid permission strings to ensure the client-side state matches the backend's capability definitions.

## Invariants

- **Returns `Permission[]`** — the response is a flat array of permission identifier strings.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token; this is not a public endpoint.
- **Endpoint is `/api/roles/permissions/all`** — follows the standard roles API pathing.

## Gotchas

- **Direct dependency for `RoleDialog`** — `RoleDialog` in `role-dialog.tsx` relies on this to render the available permission options. If this returns an empty array or an unexpected shape, the admin interface for assigning roles will fail to present selectable options.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Used by the `RoleDialog` component to populate permission selection lists.

## External consumers

None known.

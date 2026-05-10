---
node_id: concorda-web::src/lib/api.ts::adminApi.updateUser
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 10bb19934a6c3d4dd0c1c98c11a465d9946e96945f9a84656145ab8850d8e94b
status: current
---

# adminApi.updateUser

## Purpose

Provides the interface for updating existing user profiles via the admin dashboard. It is a specific method within the `adminApi` object, distinct from `createUser` (which uses `POST`) and `changePassword` (which targets a specific sub-resource). Use this when an administrator needs to modify user metadata or account details through the `AdminUsersPage` or `UserDialog`.

## Invariants

- **HTTP Method is `PUT`** — Uses the `PUT` verb to signal a full or partial update of the user resource.
- **Targets a specific user ID** — The `id` parameter is a required part of the URL path: `/api/admin/users/${id}`.
- **Returns `UserUpdateResponse`** — The response shape is strictly typed to the result of the update operation.
- **Requires Authentication** — Calls `fetchApiAuthenticated`, meaning a valid bearer token must be present in the request headers.

## Gotchas

- **Requires Admin privileges** — Because it uses `fetchApiAuthenticated`, the caller must possess an admin-level session; failure to do so results in a 401 or 403.
- **Dependency on `AdminUsersPage`** — The `AdminUsersPage` (page.tsx:129) relies on this method for its primary state updates; changes to the signature will break the main admin user management view.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Audit**: Y (Updates to user records via this endpoint are typically tracked in the backend audit logs).
- **Side effects**: Updates to user data here will propagate to any views displaying user details, such as the `UserDialog` in `admin/user-dialog.tsx`.

## External consumers

None known.

---
node_id: concorda-web::src/lib/api.ts::adminApi.deleteUser
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 33374426516b13855cd51e29b7e1b610c2529b4b813ceaf682eeb60da813c2be
status: current
---

# adminApi.deleteUser

## Purpose

The `deleteUser` method provides a way to permanently remove a user from the system via the admin API. It is a destructive operation that targets a specific user ID. Use this method when an administrator needs to revoke access and remove a user record entirely, rather than just updating user attributes or changing passwords.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb.
- **Endpoint Path** — Targets `/api/admin/users/${id}`.
- **Returns a success message** — On success, the API returns an object with a `{ message: string }` shape.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the bearer token is present and valid.

## Gotchas

- **Destructive Action** — This is a permanent deletion. There is no "soft delete" or "deactivate" state implemented in this specific method; once called, the user record is gone.

## Cross-cutting concerns

- **Auth**: Requires a valid admin session via `fetchApiAuthenticated`.
- **Audit**: Deleting a user is a high-privilege action; ensure any UI-side confirmation-dialogs are strictly guarded by admin permissions.
- **Side effects**: Deleting a user may impact other administrative views, such as the `AdminUsersPage` in `src/app/members/admin/users/page.tsx`.

## External consumers

None known.

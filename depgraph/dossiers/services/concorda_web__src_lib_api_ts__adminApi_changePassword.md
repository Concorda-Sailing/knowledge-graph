---
node_id: concorda-web::src/lib/api.ts::adminApi.changePassword
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8b16ee1bc329b6fc4e326fabf3dd9c0e71b8153e95b5060186ebaa973e954fec
status: llm_drafted
---

# adminApi.changePassword

## Purpose

Provides a way to update a user's password via the admin API. It targets a specific user by `id` and sends the new password in a JSON body. This is a specialized administrative action distinct from `updateUser`, which handles general profile data.

## Invariants

- **HTTP Method is `PUT`** — follows the pattern for idempotent updates to a specific resource sub-path.
- **Endpoint path is `/api/admin/users/${id}/password`** — the password change is treated as a sub-resource of the user.
- **Payload shape is `{ new_password: string }`** — the key must be `new_password` to match the backend expectation.
- **Returns a success message** — the expected return type is `{ message: string }`.

## Gotchas

- **Requires `fetchApiAuthenticated`** — this is an administrative action; the caller must have a valid bearer token with sufficient permissions to access the `/api/admin/` namespace.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request carries the necessary administrative credentials.
- **Audit**: As an administrative user-management action, this is a high-value target for audit logging on the backend.
- **Side effects**: Changing a password may invalidate active sessions or require users to re-authenticate depending on the backend session management implementation.

## External consumers

- `AdminUsersPage` in `src/app/members/admin/users/page.tsx`.

## Open questions

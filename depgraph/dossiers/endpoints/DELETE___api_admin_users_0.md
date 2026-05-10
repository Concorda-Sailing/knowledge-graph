---
node_id: DELETE::/api/admin/users/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 92ce181bc372a3ae98d416f955f61338df6d38071b54f18a99b994bfee0be5de
status: llm_drafted
---

# DELETE /api/admin/users/{user_id}

## Purpose

Permanently removes a user from the system. This is a destructive operation that performs a cascading cleanup of user-related associations to ensure data integrity. Use this instead of the `deactivate/reactivate` pattern when a user must be fully purged from the database.

## Invariants

- **HTTP Method: `DELETE`** — targets `/api/admin/users/{user_id}`.
- **Requires `require_auth`** — the caller must be an authenticated user.
- **Requires `_require_can_modify_user`** — the `current_user` must have sufficient permissions to modify the target `user`.
- **Cascades deletions** — explicitly deletes `UserRole` and `PersonProduct` entries associated with the `user_id` before deleting the `Person` record.
- **Returns success message** — on successful deletion, returns `{"message": "User deleted successfully"}`.

## Gotchas

- **Security/Privilege Escalation** — per commit `650233f`, this endpoint is a sensitive target for privilege escalation. Ensure any changes to the user-modifying logic do not bypass the `_require_can_modify_user` check.
- **Deactivation vs. Deletion** — commit `1c61ff5` and `5b632f2` show a history of reverting/fixing the `deactivate/reactivate` pattern. Do not use this endpoint for temporary user suspension; use the `UserUpdate.deactivated` pattern instead.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_require_can_modify_user`.
- **Side effects**: Deleting a user removes their `UserRole` and `PersonProduct` associations, which may affect roster counts or membership-based views in the dashboard.

## External consumers

- `concorda-web::src/lib/api.ts::adminApi.deleteUser`

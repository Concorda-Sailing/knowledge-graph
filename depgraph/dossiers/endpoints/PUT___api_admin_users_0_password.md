---
node_id: PUT::/api/admin/users/{0}/password
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f301fde26b716a711af138f18a52e1f41aa63cca2e5ad84edc97d4cd0f38d635
status: llm_drafted
---

# PUT /api/admin/users/{user_id}/password

## Purpose

Provides an administrative endpoint to update a specific user's password. This is a high-privilege action used by administrators to reset credentials when a user is locked out or requires manual intervention. It is distinct from the standard user profile update endpoints as it specifically handles the `hash_password` logic and requires the `_require_can_modify_user` authorization check.

## Invariants

- **HTTP Method:** `PUT`
- **Path:** `/api/admin/users/{user_id}/password`
- **Auth Requirement:** Requires a valid `AuthUser` via `require_auth`.
- **Authorization Guard:** Must pass `_require_can_modify_user` to ensure the requester has administrative rights over the target user.
- **Input Shape:** Expects a `PasswordChange` object containing the `new_password` string.
- **Return Shape:** Returns a JSON object with a success message: `{"message": "Password changed successfully"}`.

## Gotchas

- **Privilege Escalation Risk:** Per commit `650233f`, this endpoint is a target for privilege escalation attempts. Any change to the `_require_can_modify_user` logic or the dependency injection must be strictly audited to ensure only authorized admins can trigger this.
- **Database Transaction:** The password change is a direct mutation of the `Person` model's `password_hash` field. If the `db.commit()` fails, the password remains unchanged.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and the internal `_require_can_modify_user` guard.
- **Audit**: Y (Implicitly via the admin action, though no explicit log row is written in this specific function body, it falls under the admin-action umbrella).
- **Side effects**: Changing a password may affect the user's ability to authenticate in subsequent sessions, but does not trigger a logout of existing sessions unless the JWT/session invalidation logic is triggered elsewhere.

## External consumers

- `concorda-web::src/lib/api.ts::adminApi.changePassword`

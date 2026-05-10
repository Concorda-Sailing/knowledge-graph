---
node_id: PUT::/api/admin/users/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f8534fae158efd1889464e23eebe9138302af754ca578b08176720e4940d1724
status: llm_drafted
---

# PUT /api/admin/users/{user_id}

## Purpose

Updates an existing user's profile information, including identity details, product associations, and preference settings. It is the primary endpoint for administrative user management, distinct from the authentication flow which handles credentials.

## Invariants

- **HTTP Method**: `PUT`
- **Path**: `/api/admin/users/{user_id}`
- **Auth**: Requires `require_auth` and passes through `_require_can_modify_user` to ensure the requester has sufficient permissions.
- **Email Uniqueness**: If the email is being changed, the endpoint validates that the new email is not already registered to another user.
- **Role Escalation Protection**: Prevents users from assigning roles with a higher `level` than the `assigner_max_level` of the current user.
- **Deactivation Logic**: Setting `deactivated: true` sets the `leave_date` to the current UTC time.

## Gotchas

- **Privilege Escalation Guard**: A recent fix in commit `650233f` ("block privilege escalation in admin user endpoints") ensures that an admin cannot assign a role with a higher level than their own. This is a critical security check; do not remove the `assigner_max_level` logic.
- **Deactivation Revert**: A recent attempt to implement deactivation via `UserUpdate.deactivated` was reverted (see commit `1c61ff5`). Ensure any changes to the deactivation/reactivation flow respect the current implementation of `leave_date` and `datetime.utcnow()`.
- **Preference Nesting**: Updating preferences (e.g., `directory_opt_in`) uses `setdefault` to avoid wiping out existing keys in the dictionary, but it only updates the specific sub-keys provided.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_require_can_modify_user`.
- **Audit**: N/A (No explicit audit logging visible in this router).
- **Side effects**: Updates to `product_ids` will trigger a deletion and re-insertion of `PersonProduct` rows.

## External consumers

- `concorda-web::src/lib/api.ts::adminApi.updateUser`

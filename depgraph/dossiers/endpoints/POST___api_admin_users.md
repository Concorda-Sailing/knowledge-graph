---
node_id: POST::/api/admin/users
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 728265442fa121228f4473ca9f0134cb445b2e1b7820a9c28293205b36f396e7
status: llm_drafted
---

# POST /api/admin/users

## Purpose

Creates a new user record in the system, including their identity, credentials, and product associations. This endpoint is the primary way to provision users with specific roles and product access. It is distinct from standard registration flows as it is an administrative action that allows for the assignment of roles and the prevention of privilege escalation.

## Invariants

- **HTTP Method**: `POST`
- **Status Code**: Returns `201 Created` on success.
- **Auth Requirement**: Requires a valid authenticated session via `require_auth`.
- **Email Uniqueness**: Fails with `400 Bad Request` if the email is already registered in the `Person` table.
- **Role Hierarchy**: The `current_user` cannot assign a role with a higher `level` than their own maximum level.
- **Automatic Membership**: Always appends the `"member"` role to the `assigned_roles` list if it was not explicitly provided.
- **Return Shape**: Returns an object containing `id`, `email`, `first_name`, `last_name`, `roles` (list of strings), and a success `message`.

## Gotchas

- **Privilege Escalation Guard**: Per commit `650233f`, this endpoint contains logic to prevent an admin from assigning a role higher than their own. If you are modifying role assignment logic, ensure the `role.level` check remains intact to prevent unauthorized privilege elevation.
- **Role Assignment Reverts**: A recent attempt to handle user deactivation/reactivation via `UserUpdate` was reverted (see commit `1c61ff5` and `5b632f2`). Ensure that any logic intended to modify existing user states (like deactivation) is not accidentally implemented here, as this is strictly for creation.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` (via `current_user`).
- **Audit**: Records the `current_user.id` as the `assigned_by` field in the `UserRole` table.
- **Side effects**: Creating a user here is a prerequisite for populating the crew rosters used in event-related endpoints.

## External consumers

- `concorda-web` (via `adminApi.createUser`)
- `concorda-test` (via `ApiClient.createUser`)

---
node_id: concorda-api::models/role.py::Permission
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b3b7de812d6383704f4a6c51fd11d44c6173aceb0b5a407558dc065e9c15c8ea
status: current
---

# Permission

## Purpose

Defines the granular permissions available within the system. It acts as the atomic unit of authorization, which is then aggregated into `Role` objects via the `role_permissions` association table. Use this model when defining or validating specific capabilities (e.g., "edit_events") that are assigned to users through roles.

## Invariants

- **`id` is a UUID string.** The default value is a generated `uuid.uuid4()` cast to a string.
- **`name` is a unique identifier.** It is a 100-character string used for programmatic checks (e.g., `if user.has_permission("name")`).
- **`category` is required.** Every permission must belong to a specific functional group (e.g., "events", "billing") to ensure organized access control.
- **`display_name` is required.** This is the human-readable string shown in the UI/Admin dashboard.

## Gotchas

- **Relationship directionality.** While `Permission` is the core unit, it is linked to `Role` via a many-to-many `secondary` relationship (`role_permissions`). When adding permissions to a role, ensure the `roles` relationship on the `Permission` side is also considered if performing complex graph traversals.
- **`category` vs `name` distinction.** Developers often mistake the two; `name` is the machine-readable key, while `category` is the grouping.

## Cross-cutting concerns

- **Auth**: Directly drives the permission-based access control logic used by the API.
- **Side effects**: Changes to permission names or categories may require updates to the frontend permission-check logic to prevent UI-level access denials.

## External consumers

- `GET /api/roles/permissions/all` (used for populating role-assignment UIs).
- `PUT /api/roles/{0}/permissions` (used for updating role capabilities).

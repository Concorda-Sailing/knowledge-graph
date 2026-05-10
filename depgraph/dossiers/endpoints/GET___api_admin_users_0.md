---
node_id: GET::/api/admin/users/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5032801c32f327b660d5fd408ec42ba98c9111c3b3425ccefa585c6e242fa42e
status: current
---

# GET /api/admin/users/{user_id}

## Purpose

Retrieves a comprehensive profile for a specific user by their `user_id`. Unlike the standard user object, this endpoint aggregates identity data (email, phone, names) with organizational context, including their assigned roles and product memberships. It is the primary source for the Admin Dashboard's user detail views.

## Invariants

- **HTTP Method**: `GET`
- **Path**: `/api/admin/users/{user_id}`
- **Return Shape**: Returns a dictionary containing `id`, `email`, `first_name`, `last_name`, `phone_number`, `memberships` (list of objects with `id`, `product_id`, `name`, and `slug`), `roles` (list of strings), `preferences` (dict), and status flags (`email_verified`, `join_date`, `leave_date`, `created`, `disabled_permissions`).
- **Error State**: Returns a `404 Not Found` if the `user_id` does not exist in the `Person` table.
- **ISO Formatting**: The `created` field is returned as an ISO-formatted string; other date fields are returned as native JSON date-compatible types.

## Gotchas

- **Privilege Escalation Guard**: Per commit `650233f` (`fix(security): block privilege escalation in admin user endpoints`), any logic modifying user roles or permissions must be strictly controlled. While this is a GET endpoint, it is part of the sensitive `admin.py` router where role-assignment logic is heavily scrutinized.
- **Role/Membership Aggregation**: The endpoint performs two separate queries (one for `Person` and one for `UserRole`) to build the response. If a user has many roles or memberships, this is a single-point-of-failure for performance in the admin dashboard.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (Admin-level permissions).
- **Audit**: No direct audit logging on GET, but used by admin workflows that are subject to audit.
- **Side effects**: Data returned here populates the "User Detail" view in the admin dashboard.

## External consumers

- `concorda-web::src/lib/api.ts::adminApi.getUser`

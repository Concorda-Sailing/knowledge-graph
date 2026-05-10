---
node_id: GET::/api/persons/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c729ff9e9dace50987538e7fd764ebd07201d32b0dbfdc3d5d35acf093162da8
status: current
---

# GET /api/persons/{person_id}

## Purpose

Fetches a single person's profile by their unique ID. This endpoint is the primary way to retrieve PII (Personally Identifiable Information) for a user, including contact details and organization memberships. It is distinct from the directory endpoints which provide filtered, non-sensitive views; this endpoint returns the full `PersonRead` schema.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Strict access control**: A user can only access their own profile unless they possess `system_admin` or `org_admin` roles.
- **Returns `PersonRead` schema**: Includes sensitive fields like `phone_number` and `organization_ids`.
- **404 on missing ID**: Returns a 404 error if the `person_id` does not exist in the database.

## Gotchas

- **PII/Privilege Gaps**: Per commit `33a37a3`, this endpoint was part of a security hardening effort to ensure users cannot bypass role-based restrictions to view unauthorized person data. Ensure any changes to the `is_admin` logic do not inadvertently expose PII to non-privileged users.
- **Role-based visibility**: The visibility of certain fields (like `has_boat_management`) is determined by the `current_user`'s roles and the existence of the ID in `boat_mgmt_ids`.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and checks for `system_admin` or `org_admin` roles for elevated access.
- **Side effects**: Changes to person data (via `PUT`) trigger `PERSON_UPDATED` events, though this specific `GET` endpoint is read-only.

## External consumers

None known.

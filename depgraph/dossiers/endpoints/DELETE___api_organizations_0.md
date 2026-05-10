---
node_id: DELETE::/api/organizations/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 252d565eceff20a4dc377f6b2a025e00b4c75e13b942b463e433a24598061c34
status: current
---

# DELETE /api/organizations/{org_id}

## Purpose

Permanently removes an organization from the database. This is a high-privilege destructive action used to decommission an organization and its associated data. It is distinct from the `PUT` endpoint which updates organization details; this method performs a hard delete of the `Organization` record.

## Invariants

- **HTTP Method is `DELETE`**.
- **Requires `org_id`** as a path parameter.
- **Returns a JSON object** with the key `"message"` and value `"Organization deleted"` upon success.
- **Returns 404** if the `org_id` does not exist in the database.
- **Requires two-tier authorization**: the user must be an admin (`_require_admin`) and must have specific organizational admin scope (`_require_org_admin_scope`).

## Gotchas

- **Strict Scope Enforcement**: Per commit `058aa8c` (security: tier-C cross-org scope enforcement), this endpoint is protected by both a general admin check and a specific organization-level scope check. A user with a valid admin token but lacking the specific `org_id` scope will be blocked.
- **IDOR Vulnerability**: Recent security hardening (commit `c9a7c41`) ensures that the `_require_org_admin_scope` check is mandatory to prevent unauthorized cross-org deletions.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` and `_require_org_admin_scope`.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Deleting an organization will cause any dependent data (e.g., contacts, events, or schedules) that relies on this `org_id` to become orphaned or inaccessible, depending on database-level cascade settings.

## External consumers

- `concorda-web::src/lib/api.ts::organizationsApi.delete`

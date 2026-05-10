---
node_id: PUT::/api/organizations/{0}/contacts/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bcf5044d0845d2281df09c67be400935305f16e2689b8bd38df681479cd13306
status: current
---

# PUT /api/organizations/{org_id}/contacts/{contact_role_id}

## Purpose

Updates the contact details (name, email, phone) and their associated role for a specific organization. This endpoint is distinct from general organization updates as it manages the granular `ContactRole` relationship, allowing for the modification of a person's identity (via name splitting) and their organizational standing simultaneously.

## Invariants

- **HTTP Method is `PUT`** and requires an `org_id` and `contact_role_id`.
- **Requires `_require_admin` dependency** to ensure the caller is an authenticated admin.
- **Enforces `_require_org_admin_scope`** to ensure the admin has authority over the specific `org_id` being modified.
- **Splits name components** if `first_name` or `last_name` are provided in the payload, reconstructing the `contact.name` string.
- **Returns a `ContactWithRole` object** containing the updated state of both the `Contact` and the `ContactRole`.

## Gotchas

- **Name reconstruction logic:** The function uses `contact.name.split(" ", 1)` to derive the first part of the name before applying updates. If a name is a single word or lacks a space, the `last` part becomes an empty string, which can lead to unexpected name truncation if not handled carefully.
- **Security scope enforcement:** Per commit `058aa8c` (security: tier-C cross-org scope enforcement), this endpoint relies on `_require_org_admin_scope` to prevent cross-organization IDOR attacks. Modifying the dependency or the scope check will break the tier-C security model.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` and `_require_org_admin_scope`.
- **Rate limit**: none.
- **Audit**: Y (updates to contact identity/roles are tracked via the database session).
- **Side effects**: Updates to contact details may affect the display of contact info in the organization directory and any user-facing profile views.

## External consumers

- `concorda-web` (via `orgContactsApi.update`).

## Open questions

- The name-splitting logic is brittle (e.g., middle names or multi-part surnames). Should we move to a structured `first_name`/`last_name` schema on the `Contact` model itself to avoid string manipulation errors?

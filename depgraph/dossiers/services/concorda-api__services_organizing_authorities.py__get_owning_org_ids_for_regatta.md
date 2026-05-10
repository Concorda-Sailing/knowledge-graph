---
node_id: concorda-api::services/organizing_authorities.py::get_owning_org_ids_for_regatta
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b292a1772b442a63446886bd5f3ec68ccedcda45d115236d343aed3a85d63d0d
status: llm_drafted
---

# get_owning_org_ids_for_regatta

## Purpose

Retrieves the set of organization UUIDs that hold ownership/authority over a specific regatta. This is a core utility for enforcing multi-tenant security boundaries, ensuring that a request to modify or view a regatta is scoped correctly to the organizations that actually control it. Use this instead of `get_owning_org_ids_for_series` or `get_owning_org_ids_for_product` when the entry point of the request is a regatta UUID.

## Invariants

- **Returns a `set[str]` of UUIDs.** The result is a set of strings, not a list, to ensure uniqueness of organization IDs in the caller.
- **Filters by `OA_RELATIONSHIP`.** The query explicitly filters for the `OA_RELATIONSHIP` constant to ensure only primary organizing authorities are returned, not secondary or legacy associations.
- **Requires a valid `regatta_uuid`.** The function expects a string UUID that matches the `OrganizationRegatta` relationship table.

## Gotchas

- **Strict scope enforcement.** Per commit `058aa8c`, this logic is part of the "tier-C cross-org scope enforcement" pattern. If this function returns an empty set, the caller (likely an API endpoint) will treat the user as having no authority over the resource, even if they have general system access.
- **Relationship dependency.** The result is strictly dependent on the `relationship` column matching `OA_RELATIONSHIP`. If a regatta is associated with an organization via a different relationship type, it will be excluded from this set.

## Cross-cutting concerns

- **Auth**: Used for tier-C cross-org scope enforcement (see commit `058aa8c`).
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Controls access control for any endpoint relying on regatta-level ownership-based permissions.

## External consumers

None known.

## Open questions

- Should there be a fallback mechanism if a regatta is "orphaned" (has no entries in `OrganizationRegatta`)? Currently, it returns an empty set, which effectively locks out all organization-based access.

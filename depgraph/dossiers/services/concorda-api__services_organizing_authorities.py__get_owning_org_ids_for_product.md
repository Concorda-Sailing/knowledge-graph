---
node_id: concorda-api::services/organizing_authorities.py::get_owning_org_ids_for_product
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3c9dbafbf4e000cfa564d520afc40bf7e84cc7390a7e29ee311cd361f98cda73
status: current
---

# get_owning_org_ids_for_product

## Purpose

Determines the set of Organization IDs that have authority over a specific product by traversing the relationship from the Product to its parent Event. This is used to enforce multi-tenant security boundaries, ensuring that a product's visibility is scoped to the organizations that own the underlying event. Use this instead of `get_owning_org_ids_for_event` when you only have a `product_uuid` and need to resolve the hierarchy.

## Invariants

- **Returns a `set[str]`** — even if the product has no event or is a one-off catalog item, it returns an empty set rather than `None`.
- **Dependency on `event_id`** — the function relies on the `Product.event_id` field being populated to resolve the hierarchy.
- **Hierarchy traversal** — it transitively calls `get_owning_org_ids_for_event` to find the actual owners.

## Gotchas

- **One-off catalog items return empty sets** — per the docstring, products without an `event_id` (like standalone catalog items) return `set()`. This is a critical distinction for security logic; if a product is not tied to an event, it effectively has no "owning" organizations in this model.
- **Security Tier-C enforcement** — as seen in commit `058aa8c`, this logic is part of the tier-C cross-org scope enforcement. If this function returns an empty set, the product is effectively invisible to standard organizational lookups.

## Cross-cutting concerns

- **Auth**: Used for tier-C cross-org scope enforcement (see commit `058aa8c`).
- **Side effects**: Indirectly controls visibility of product-related data in the UI by defining the scope of "ownership."

## External consumers

None known.

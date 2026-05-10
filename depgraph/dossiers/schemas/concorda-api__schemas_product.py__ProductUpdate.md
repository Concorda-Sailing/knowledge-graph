---
node_id: concorda-api::schemas/product.py::ProductUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d27f6227c57c58674b9300c7fedffe8571f60efeac46b5c6629ff227dd5a12fa
status: llm_drafted
---

# ProductUpdate

## Purpose

The schema for partial updates to a product entity. It is used by the `PUT /api/products/{id}` endpoint to allow clients to modify specific fields (like `price` or `is_active`) without providing the full product object. It is distinct from `ProductCreate` in that all fields are `Optional`, allowing for granular updates.

## Invariants

- **All fields are `Optional`** — This allows for partial updates where only the provided fields are patched onto the existing record.
- **`price` must be a `Decimal`** — Maintains precision for financial calculations during updates.
- **`event_id` is an `Optional[str]`** — Allows re-associating a product with a different event or clearing the association.
- **`sort_order` is an `int`** — Used for ordering products within a specific view or event.

## Gotchas

- **Temporal product logic** — Per commit `6405007`, this schema is part of the new "temporal products" system. Updates to `effective_date`, `end_date`, or `publish_date` change when a product becomes visible/active in the registration flow.

## Cross-cutting concerns

- **Auth**: Handled by the `PUT /api/products/{id}` router.
- **Side effects**: Updates to this schema can affect the visibility of products in the registration system and the "temporal products" lifecycle.

## External consumers

- `PUT /api/products/{id}` (via `routers/products.py`)

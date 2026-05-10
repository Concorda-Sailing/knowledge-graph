---
node_id: concorda-api::models/temporal_product_merchandise.py::TemporalProductMerchandise
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4fd5662c88d6a18a65738508b0b43436b5546ccd2413d49b850ad19f5d84c8db
status: current
---

# TemporalProductMerchandise

## Purpose

The junction table linking `TemporalProduct` instances to specific `merchandise` items. It facilitates the many-to-many relationship required when a temporal product (a product with a specific lifecycle/timeframe) includes or requires certain physical goods. Use this model when managing the composition of products within the registration system.

## Invariants

- **`temporal_product_id` is a required UUID/String (36 chars)** and must exist in the `temporal_products` table.
- **`merchandise_id` is a required UUID/String (36 chars)** and must exist in the `merchandise` table.
- **Both columns are indexed** to support efficient lookups during product composition queries.
- **Inherits from `BaseModel`**, meaning it carries the standard `type="TemporalProductMerchandise"` metadata in its constructor.

## Gotchas

- **Direct dependency in deletion:** Per `routers/temporal_products.py:341`, deleting a `TemporalProduct` via `DELETE /api/temporal-products/{id}` relies on the database/ORM handling the removal of these junction records. If this relationship is not handled via cascade or explicit deletion, orphaned rows may persist in the database.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Deletion of a `TemporalProduct` triggers the removal of these associations.

## External consumers

- None known.

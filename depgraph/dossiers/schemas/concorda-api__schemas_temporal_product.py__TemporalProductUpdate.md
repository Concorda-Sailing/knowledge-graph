---
node_id: concorda-api::schemas/temporal_product.py::TemporalProductUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ceb13403eca734607654d01ba1d54506e86a085c77e2ae841413610fa9c7c84a
status: llm_drafted
---

# TemporalProductUpdate

## Purpose

The schema for partial updates to a temporal product. It allows a client to send a subset of fields (via `Optional` types) to modify an existing product's metadata, pricing, or eligibility flags. Use this instead of `TemporalProductRead` or `TemporalProductPublic` when performing a `PATCH` or `PUT` operation to avoid requiring the full object state.

## Invariants

- **All fields are `Optional`** — This allows for partial updates where only the changed fields are transmitted.
- **`price` uses `Decimal`** — Maintains precision for financial calculations to avoid floating-point errors.
- **`merchandise_ids` is a `list[str]`** — Expects a list of strings for product-linked merchandise.
- **`event_id` is a string** — Links the temporal product to a specific event context.

## Gotchas

- **Role-based restructuring** — Per commit `bb2da2b`, the schema is part of a recent restructuring of memberships and roles (including `event_manager`). Ensure that updates to eligibility flags like `grants_crewfinder` or `grants_boat_management` are validated against the user's permission level in the router.

## Cross-cutting concerns

- **Auth**: Handled by the `PUT /api/temporal-products/{0}` endpoint; requires appropriate event management permissions.
- **Side effects**: Updates to this schema may affect the visibility of products on the registration page and the calculation of event-specific discounts.

## External consumers

- `PUT /api/temporal-products/{0}` in `routers/temporal_products.py`.

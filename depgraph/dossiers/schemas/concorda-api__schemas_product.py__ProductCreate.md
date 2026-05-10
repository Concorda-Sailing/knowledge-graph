---
node_id: concorda-api::schemas/product.py::ProductCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d47c6f18e07e10d1c0d74ed25333b7f703433e575bdaf03285a2b46537273b9a
status: llm_drafted
---

# ProductCreate

## Purpose

The Pydantic model used to validate the creation of a new product via the API. It is distinct from `ProductUpdate` (which allows all fields to be optional) and `ProductRead` (which includes system-generated fields like `id` and `created`). Use this when implementing `POST` endpoints for product creation to ensure required fields like `name`, `slug`, and `price` are present.

## Invariants

- **`name` and `slug` are required strings.** They cannot be omitted during creation.
- **`price` must be a `Decimal`.** This ensures precision for financial calculations and avoids floating-point errors.
- **`event_id` is an optional string.** It links the product to a specific event context if applicable.
- **`sort_order` defaults to `0`** if not provided, ensuring a predictable initial position in lists.

## Gotchas

- **Temporal product logic.** Per commit `6405007`, this schema supports "temporal products" via `effective_date`, `end_date`, and `publish_date`. Ensure that logic handling these dates accounts for the fact that a product can exist in the database but remain "inactive" or "unpublished" based on the current date.

## Cross-cutting concerns

- **Auth**: Handled by the router level (likely requiring admin/owner permissions to POST to `/api/products`).
- **Side effects**: Creating a product via this schema will populate the product registry used by the registration system and payment flows.

## External consumers

None known.

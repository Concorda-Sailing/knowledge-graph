---
node_id: concorda-api::schemas/merchandise.py::MerchandiseCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d9f2ff106937061c68bcee048c89af72902d3ec5595b73284a35966f58a63768
status: llm_drafted
---

# MerchandiseCreate

## Purpose

The schema for creating new merchandise items via the API. It defines the required and optional fields for the initial ingestion of a product, distinguishing itself from `MerchandiseUpdate` (which makes all fields optional for partial updates) and `MerchandiseRead` (which includes system-generated fields like `id` and `created`). Use this when implementing new POST endpoints for product creation.

## Invariants

- **`name` and `slug` are required strings.** Unlike the update schema, these cannot be omitted during creation.
- **`price` must be a `Decimal`.** This ensures precision for financial transactions and avoids floating-point errors in the database.
- **`sort_order` defaults to `0` if not provided.** This is an integer used for ordering items in the UI.
- **`is_active` defaults to `True`.** New items are active by default unless explicitly set otherwise.

## Gotchas

- **Recent expansion of product types.** Per commit `6405007`, this schema is part of the new "temporal products" and "registration system" expansion. Ensure that any logic involving `MerchandiseCreate` accounts for the fact that products may now be tied to specific event lifecycles.

## Cross-cutting concerns

- **Auth**: Dependent on the `POST /api/merchandise` router; requires appropriate administrative permissions to execute.
- **Side effects**: Creation of a merchandise item may impact the visibility of items in the registration system and the availability of items in the payments flow.

## External consumers

- `POST /api/merchandise` (internal API endpoint).

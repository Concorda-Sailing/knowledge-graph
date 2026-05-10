---
node_id: concorda-api::schemas/merchandise.py::MerchandiseUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b1f072d30ee20fd15ba4798686522fa21eaae035488b258573b22f52bcf77150
status: current
---

# MerchandiseUpdate

## Purpose

The schema for partial updates to a merchandise item. Unlike `MerchandiseRead`, which represents the full state, `MerchandiseUpdate` makes all fields optional to support PATCH-style updates via the `PUT /api/merchandise/{0}` endpoint. Use this when implementing logic that modifies existing stock, pricing, or availability without requiring a full object payload.

## Invariants

- **All fields are `Optional`** — This allows for partial updates where only the changed fields are sent.
- **`price` uses `Decimal`** — Maintains precision for financial calculations, matching the `MerchandiseRead` contract.
- **`slug` is a string** — Used as the unique identifier/URL component in the API path.

## Gotchas

- **`price` and `quantity` precision** — While `MerchandiseUpdate` allows these to be `None`, the underlying database/`MerchandiseRead` expects specific types; ensure the consumer handles the transition from `Optional[Decimal]` to the required `Decimal` in the database.

## Cross-cutting concerns

- **Auth**: Handled by the `PUT /api/merchandise/{0}` router.
- **Side effects**: Updates to this schema via the merchandise router may affect the visibility of items in the storefront/product listing.

## External consumers

- `PUT /api/merchandise/{0}` (via import in `routers/merchandise.py:78`).

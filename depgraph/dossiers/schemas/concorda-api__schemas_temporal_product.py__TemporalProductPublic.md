---
node_id: concorda-api::schemas/temporal_product.py::TemporalProductPublic
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 482f7c19e30481e70ef437b98fd9a0547b39174d38d698c239db257980024805
status: llm_drafted
---

# TemporalProductPublic

## Purpose

The public-facing schema for temporal products used on the registration page. It provides a sanitized view of product data, specifically highlighting eligibility flags (e.g., `grants_crewfinder`, `grants_prize_eligibility`) that determine how a product interacts with the registration flow. Use this schema instead of `ProductCreate` or internal product models when building endpoints for the public-facing registration/discovery side of the app.

## Invariants

- **`id` and `slug` are required strings.** The `slug` is the primary identifier used for URL routing in the registration frontend.
- **`price` is a `Decimal`.** This ensures precision for financial calculations and prevents floating-point errors during checkout.
- **`from_attributes = True`** — The model is designed to be instantiated directly from ORM objects (e.g., SQLAlchemy models).

## Gotchas

- **Role-based permission changes:** Per commit `bb2da2b`, the structure of product-related permissions and roles was recently refactored to fix a permissions bug. Ensure that any logic relying on the `grants_*` boolean flags is compatible with the new `event_manager` role structure.

## Cross-cutting concerns

- **Auth**: None (this is a public-facing schema used by the `GET /api/temporal-products/available` endpoint).
- **Side effects**: Changes to this schema or its boolean flags will directly affect the visibility and eligibility logic on the registration page.

## External consumers

- Web-based registration frontend (via `GET /api/temporal-products/available`).

---
node_id: concorda-api::schemas/temporal_product.py::TemporalProductCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65bde58ab0f2b9624c0de601c8b592dab73a3b65e258b879f8b267188544b7d0
status: current
---

# TemporalProductCreate

## Purpose

The schema for creating a new temporal product (e.g., a specific year's membership or an event-linked registration). It is distinct from `ProductCreate` by including temporal attributes like `year`, `start_date`, and `end_date`, and by providing specific boolean flags for feature access (e.g., `grants_crewfinder`). Use this when the product lifecycle is tied to a specific time-bound event or a specific calendar year.

## Invariants

- **`year` defaults to the current year** via the `default_year` validator if not provided.
- **`category` defaults to `"Membership"`** if not explicitly set.
- **`price` must be a `Decimal`** to ensure precision for financial transactions.
- **`slug` and `name` are required strings**; they cannot be null or omitted.
- **`is_active` defaults to `True`** to ensure newly created products are immediately available unless specified otherwise.

## Gotchas

- **The `year` validator uses `date.today().year`** — if this schema is used in a background job or a system with a non-standard clock, the "default" year might shift unexpectedly.
- **Recent restructuring of roles and permissions** (see commit `bb2da2b`) suggests that the relationship between these products and user roles (like `event_manager`) is highly sensitive to the `category` and `grants_*` flags.

## Cross-cutting concerns

- **Auth**: Handled by the `POST /api/temporal-products` endpoint (see `routers/temporal_products.py`).
- **Side effects**: Creation of these products impacts the availability of registration options for specific events and may trigger updates to the `event_manager` role-based access control logic.

## External consumers

- N/A — internal to the `concorda-api` service.

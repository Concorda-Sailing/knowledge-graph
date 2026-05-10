---
node_id: concorda-api::schemas/temporal_product.py::TemporalProductRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 899b38c3481b06686754d2e5b8d3ec6a1865c60dffabf0d01a55348c00ffcccb
status: current
---

# TemporalProductRead

## Purpose

Backend Pydantic admin read schema for a `TemporalProduct` row — the full, wide shape returned by every admin-facing endpoint that exposes a temporal product (memberships, event-scoped registration SKUs). It carries everything the catalog UI needs to render and edit a row: identity (`id`, `slug`, `year`, `category`), pricing (`price`), the date window (`start_date`/`end_date`), display state (`sort_order`, `is_active`), gating inputs (`requires_boat`, `min_age`, `max_age`, `event_id`), the four `grants_*` entitlement flags, and the nested `merchandise: list[MerchandiseRead]` join. This is the wide-shape counterpart to `TemporalProductPublic` (narrower, unauthenticated, no grants/no merchandise/no dates) — the two schemas are the auth boundary expressed in types.

## Invariants

- All six admin endpoints in `routers/temporal_products.py` use this as `response_model`: `GET /api/temporal-products`, `GET /api/temporal-products/{id}`, `POST /api/temporal-products`, `PUT /api/temporal-products/{id}`, `POST /api/temporal-products/{id}/duplicate`, `POST /api/temporal-products/duplicate-year`. Any new admin temporal-product endpoint should return this schema, not invent a third shape.
- The four `grants_*` fields default to `False` at the schema level — but in practice every row coming from the ORM has explicit values. Don't lean on the default; the truth is in the DB column.
- `merchandise` defaults to `[]` and is populated by the router's `_product_to_read` / `_products_to_read` helpers (`routers/temporal_products.py:59-94`), **not** by ORM relationship traversal — the helpers do an explicit query and inject the list. `model_validate(product)` alone leaves it empty.
- `from_attributes = True` — accepts ORM objects directly. Don't switch to dict-construction without auditing the router helpers above.
- `type: str` is the polymorphic discriminator (`"TemporalProduct"` hard-coded in the model `__init__`). Always present on read; downstream clients can rely on it.
- `year: int` is non-optional on read (the model auto-populates if null on create). Don't relax to `Optional` without rolling forward the TS client type.

## Gotchas

- **`merchandise` is the only field that requires the helper to be populated.** A handler that constructs `TemporalProductRead.model_validate(product)` directly (skipping `_product_to_read`) returns `merchandise: []` even when the join exists. Reviewers should grep new handlers for this pattern.
- **`TemporalProductPublic` is intentionally narrower** — no `grants_*`, no `event_id`, no dates, no merchandise. If you add a field here, decide deliberately whether it also belongs in the public shape; defaulting to "add to both" leaks entitlement info to anonymous callers (`temporalProductsApi.getAvailable` dossier covers the auth boundary).
- **`type` is in this schema but not in `TemporalProductCreate`/`Update`.** Round-tripping a Read through Create requires dropping `type`, `created`, `modified`, `id`, and the wider derived shape — there's no fromRead helper.
- **`grants_*` field name drift would silently break the SPA.** The TS `TemporalProduct` type in `concorda-web/src/lib/api.ts` mirrors these exact names; the `adminTemporalProductsApi.list` consumer reads `grants_boat_management` etc. directly. Renaming on the backend without coordinating the TS type causes silent `undefined` reads in the admin catalog UI.

## Cross-cutting concerns

- **Auth**: every endpoint returning this schema is gated by `admin.memberships.view` or `admin.memberships.manage`. This schema must never leak through an unauthenticated endpoint — that's `TemporalProductPublic`'s job.
- **Entitlement contract surface**: the four `grants_*` fields are the wire form of the capability contract documented in the TemporalProduct model dossier — flipping one in the admin UI rewrites runtime behavior across `services/approvals.py`, `routers/profile.py`, `routers/persons.py`, `routers/payments.py`, `routers/auth.py`.
- **Year-rollover side effect**: the `GET /api/temporal-products` handler can mint a year's worth of rows via `_copy_products_from_previous_year` before returning them as `list[TemporalProductRead]` — see `adminTemporalProductsApi.list` dossier. The schema itself is pure data, but the endpoints returning it are not all idempotent.
- **No websocket broadcast** on admin temporal-product CRUD; the SPA refetches. If broadcasts are added later, this schema is the natural payload shape.
- **Merchandise coupling**: changes to `MerchandiseRead` flow into every consumer of this schema. Treat the two as a pair when versioning.

## External consumers

None directly. All six dependent endpoints are admin-only and consumed by `concorda-web` admin pages via `adminTemporalProductsApi.{list,get,create,update}` and the duplicate/duplicate-year flows. The iOS Expo app uses `temporalProductsApi.getAvailable` (public, returns `TemporalProductPublic`) and does not see this shape.

## Open questions

- Should `grants_*` schema-level defaults be removed (forcing explicit values) to catch handlers that bypass the ORM and forget to set them? Current `= False` defaults silently mask a bug class.
- Should there be an explicit `TemporalProductReadWithStats` for admin pages that want usage counts (active PersonProduct count, lifetime revenue), or should those live on a sibling endpoint? Currently admins compute this client-side after a separate fetch.

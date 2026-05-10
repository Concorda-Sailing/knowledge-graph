---
node_id: concorda-api::schemas/product.py::ProductRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 82339f7de0689b282a4f78112e233699ad080a872f09413750e7ac9f6d4555bf
status: llm_drafted
---

# ProductRead

## Purpose

`ProductRead` is the Pydantic response schema for the **admin event-ticket CRUD surface** under `/api/products`. Every row it serializes is a single buyable SKU from the `Product` table — discrete event tickets, dinner add-ons, late fees — never a membership (those are `TemporalProduct`). When a future Claude is shaping admin ticket-management UI, debugging product CRUD responses, or adding fields to the SKU catalog, this is the wire contract. Note: the *public* event-detail endpoints (`GET /events/slug/{slug}/tickets`) return a hand-rolled dict, **not** `ProductRead` — so this schema is admin-facing only, despite what the frame suggests.

## Invariants

- **`from_attributes = True`** — populated by SQLAlchemy ORM instances directly. Don't pass dicts; the router returns the ORM `Product` and lets Pydantic walk attributes.
- **`type: str` is always `"Product"`** — see Product model dossier: hard-coded in `__init__`. Clients can rely on this discriminator to distinguish from `TemporalProductRead` payloads.
- **`id` is `str` (UUID), not int.** Matches `BaseModel.id` convention across the API.
- **`price: Decimal` (required, not Optional)** — serialized as a JSON string by default. Frontends must parse, not multiply with raw floats. `quantity` is optional and represents inventory cap, not a stock counter (see Product dossier — sold-out is computed from `EventRegistration` count, not decremented here).
- **`sort_order` and `is_active` are required** in Read but optional in `ProductCreate` (defaults `0` / `True`) — round-tripping a Read back through Create works; round-tripping through Update is partial-update only.
- **Field set is a strict superset of `ProductCreate`/`ProductUpdate`** plus `id`, `type`, `created`, `modified`. Keep all three schemas in lockstep when adding columns.

## Gotchas

- **Only one commit has ever touched this file** (`6405007`, the bootstrap). No revert history, no hard-learned bug — but also no battle-testing beyond initial scaffolding. Treat changes here as load-bearing for the admin UI even though git history looks quiet.
- **`effective_date`, `end_date`, `publish_date` are serialized but nothing reads them.** The Product dossier flags this — three columns plumbed through the schema with zero enforcement anywhere. A future Claude removing them from the model must also remove them here and from `ProductCreate/Update`, or Pydantic will fail on `from_attributes`.
- **The public ticket-list endpoint emits a *different* shape.** `GET /events/slug/{slug}/tickets` returns custom dicts with computed `sold_out`/`available` fields not present on `ProductRead`. Don't assume the schema is the canonical wire format — admin and public diverge.
- **Hard-deleted Products leave dangling FKs.** `Transaction.product_id` and `EventRegistration.product_id` may point at a now-missing id; callers walking those tables and trying to fetch via `GET /api/products/{id}` get a 404. Confirmation flows defend with `product.name if product else "Unknown"` — don't mirror that pattern into `ProductRead` (it would mask the deletion).
- **`Decimal` JSON serialization differs from `float`.** A frontend that previously consumed a hand-coded dict with `price: number` will break when switched to `ProductRead`'s stringified Decimal. Confirm the client parses.

## Cross-cutting concerns

- **Auth.** Every dependent endpoint is gated by `require_permission("events.edit")` *plus* the tier-C `_require_event_org_scope` check on create/update (`routers/products.py:20-31`). Update re-checks against the *destination* `event_id` to prevent a delegate from reassigning a ticket into another club's event.
- **No websocket broadcast** on product mutations — the SPA refetches.
- **No audit trail** beyond `created`/`modified` columns (returned in the schema). No `created_by`/`modified_by`.
- **Stripe coupling is indirect.** `ProductRead` itself never reaches Stripe — `routers/payments.py` reads the ORM Product and copies `id`/`slug`/`name` into PaymentIntent metadata. Renaming a field here does not break Stripe; renaming the underlying *column* does.
- **No rate limiting** on these CRUD endpoints; they're admin-only.

## External consumers

- **concorda-web admin UI** — product management screens consume all four dependent endpoints. Field renames here are breaking changes for the SPA.
- **Concorda iOS app** — does **not** call these admin endpoints; it reads the public `/events/slug/{slug}/tickets` shape (which is not `ProductRead`).
- **No external webhooks, scheduled jobs, or third-party integrations** read `ProductRead`. Stripe sees only metadata copies, not the schema.

## Open questions

- **Should the public ticket endpoint switch to `ProductRead` (plus computed fields)?** Two shapes for the same row creates drift risk; a `ProductPublicRead` extending `ProductRead` would unify them.
- **Should `effective_date` / `end_date` / `publish_date` be dropped from the schema?** Same question as the Product model — if the columns go, the schema fields must follow. If they stay and get enforced, `ProductRead` should probably also surface a computed `is_published` so clients don't re-implement the window logic.
- **Versioning story.** No `Config.extra` policy declared. Adding a field is safe; renaming or removing one is a silent client break with no deprecation path.

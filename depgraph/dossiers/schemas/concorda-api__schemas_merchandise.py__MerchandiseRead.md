---
node_id: concorda-api::schemas/merchandise.py::MerchandiseRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: da54574788a1accb7c7444ac9771114e2ba459a6faa9b06af0ccdf492ecfd50f
status: current
---

# MerchandiseRead

## Purpose

Pydantic response schema for the `Merchandise` SQLAlchemy model — the wire shape that every merchandise read returns. Used directly by the four admin CRUD endpoints under `/api/merchandise` and, more consequentially, embedded as `list[MerchandiseRead]` inside `TemporalProductRead` (see `schemas/temporal_product.py:7,93`) so any temporal-product fetch bundles its merchandise. If you're deciding what fields a client can see for a merchandise item, this schema is the single source of truth; changing it changes both the merchandise endpoints and every temporal-product response.

## Invariants

- Field set must stay a strict superset of `MerchandiseCreate`/`MerchandiseUpdate` minus the auto-managed columns (`id`, `type`, `created`, `modified`) — the three schemas are hand-kept in sync, there is no shared base.
- `name`, `slug`, `price`, `sort_order`, `is_active` are non-Optional here even though `sort_order` and `is_active` have DB defaults — the model guarantees they are populated by the time a read serializes.
- `type: str` echoes the `BaseModel` discriminator hardcoded to `"Merchandise"`; clients may key off it when discriminating polymorphic product lists.
- `from_attributes = True` (Pydantic v2) is required because the router returns ORM instances directly, not dicts.
- `price` must serialize as `Decimal` end-to-end (mirrors the `002_float_to_decimal` migration on the model); never relax to `float`.

## Gotchas

- **`image_url` vs `additional_data` drift.** The Merchandise model dossier flags that migration `040_schema_redesign` moved image URLs into the `additional_data` JSON bag, but this schema still exposes only `image_url` and does not surface `additional_data` at all. Reads return the legacy column, writes go to the legacy column, and the JSON bag is invisible to API consumers. Any reconciliation needs to touch `MerchandiseCreate`, `MerchandiseUpdate`, and this class together.
- **Embedded in `TemporalProductRead`.** Renaming or removing a field here silently changes temporal-product responses — that path is exercised by membership purchase flows, so a schema change without grepping `temporal_product.py` will break more than the merchandise endpoints.
- Only one commit (`6405007`) ever touched this file; the area is quiet, which is why the `image_url` drift has lingered.
- No `quantity` semantics are documented — `None` could mean "unlimited" or "unknown"; the schema permits either interpretation and the router doesn't decrement on purchase.

## Cross-cutting concerns

- **Auth:** every endpoint returning this schema requires `admin.memberships.view` or `admin.memberships.manage` — there is no public read path today. If merchandise ever surfaces on a member-facing storefront, audit which fields (e.g. `stock_number`, `quantity`) should remain admin-only before relaxing the gate.
- **Bundle coupling:** `TemporalProductRead.merchandise: list[MerchandiseRead]` means this schema rides on every temporal-product response — including read paths whose auth posture differs from `/api/merchandise`.
- No websocket events, no `ActivityLog` entries, no rate-limit ties.
- `created`/`modified` serialize as naive datetimes (predates the `UtcDateTime` convention); frontend should treat them as UTC.

## External consumers

None known. No Expo app screens, scheduled jobs, or webhooks consume `MerchandiseRead` today. The only embedded consumer is `TemporalProductRead` inside the same backend.

## Open questions

- Should `additional_data` be exposed (replacing or supplementing `image_url`) so the schema matches the migrated model state?
- Should `MerchandiseRead` used inside `TemporalProductRead` be a slimmed projection (e.g. drop `quantity`, `stock_number`) to avoid leaking inventory data through the bundle path if temporal-product reads ever become member-facing?

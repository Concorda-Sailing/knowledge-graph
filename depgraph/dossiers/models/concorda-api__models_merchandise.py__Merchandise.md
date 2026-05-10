---
node_id: concorda-api::models/merchandise.py::Merchandise
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b60410616e73b5d10d7d225e51ef491a8fc58137a689c458f3e5f1feec2fd46
status: llm_drafted
---

# Merchandise

## Purpose

Backend SQLAlchemy model representing a non-temporal product — physical/sellable merchandise (shirts, hats, burgees, etc.) that an org offers alongside memberships and event tickets. Unlike `TemporalProduct` (memberships, season passes — anything date-bounded), a `Merchandise` row is a plain catalog item with `price`, `quantity`, `slug`, and a free-form `additional_data` JSON bag. Merchandise gets pulled into purchase flows by being associated to a `TemporalProduct` through the `TemporalProductMerchandise` junction — e.g. "the Family Membership includes a burgee" — so this table is the source of truth for the item itself while the junction expresses bundling. If you're deciding where to put a new sellable-good attribute, this is the right place; if it's something that grants access for a season, it belongs on `TemporalProduct` instead.

## Invariants

- `slug` is globally unique (DB-enforced `unique=True` plus app-layer recheck in POST/PUT).
- `stock_number` uniqueness is app-layer-only — there is no DB unique index, so a race could insert duplicates.
- `price` is `Numeric(10,2)`; never store as float. Migration `002_float_to_decimal.py` did the conversion and any new numeric column on this table must follow.
- `__init__` hard-codes `type="Merchandise"` for the BaseModel discriminator — don't override.
- `additional_data` (JSON) is the canonical home for image URLs and any future loose attributes; `image_url` is a legacy column kept only so existing SQLite files don't break.

## Gotchas

- **`image_url` is legacy but still in the API.** Migration `040_schema_redesign.py` moved `image_url` values into `additional_data` (as `{"image_url": ...}`), yet `MerchandiseCreate/Update/Read` schemas still surface `image_url` and don't surface `additional_data` at all. Writes to `image_url` via the router land in the legacy column and are *not* synced to `additional_data`; reads pull from the legacy column. Any consumer expecting the JSON bag will see stale data until this is reconciled.
- **No FK cleanup on delete.** `DELETE /api/merchandise/{id}` does a plain `db.delete(item)` with no cascade. `TemporalProductMerchandise` rows pointing at the deleted merchandise are orphaned (their FK has no `ondelete`), and `routers/temporal_products.py` will silently drop them from its `Merchandise.id.in_(merch_ids)` lookup.
- **Slug/stock_number conflict checks are split.** POST checks both; PUT checks both but only excludes the current row — fine, but the two queries aren't atomic, so concurrent writes can both pass and one will fail on commit (for slug) or succeed-with-duplicate (for stock_number).
- Only two commits ever touched this file (`6405007` initial, `ee82e42` schema redesign). The drift above hasn't been fixed because the area is quiet.

## Cross-cutting concerns

- **Auth:** all five endpoints require permissions `admin.memberships.view` (GET) or `admin.memberships.manage` (POST/PUT/DELETE). There is no public/member-facing read path — merchandise is admin-only catalog management today.
- **Bundling side-effects:** changes here cascade through `routers/temporal_products.py`, which embeds `MerchandiseRead` in `TemporalProductRead` via the junction. Renaming/removing a field on `MerchandiseRead` breaks temporal product responses too.
- **No audit log, no websocket events, no rate limiter touchpoint.** Mutations are not recorded in `ActivityLog`.
- `modified` is manually set in PUT (`item.modified = datetime.utcnow()`) even though `BaseModel.modified` has `onupdate=datetime.utcnow` — redundant but harmless; uses naive UTC, not the `UtcDateTime` convention (predates it).

## External consumers

None known. No Expo app screens consume merchandise, no scheduled jobs touch the table, and the only internal consumer beyond the five router endpoints is the temporal-products bundling read path.

## Open questions

- Should the API drop `image_url` from schemas and expose `additional_data` directly, or keep `image_url` as a virtual field that reads/writes through the JSON bag? Current state is the worst of both worlds.
- Is admin-only the intended posture forever? If merchandise ever shows on a public storefront, the permission gate on GET needs to relax and the schemas need to stop leaking admin-only fields.
- Should deletion be a soft-delete (`is_active=False` only) given the orphan-junction risk, or should we add `ondelete="CASCADE"` to `TemporalProductMerchandise`?

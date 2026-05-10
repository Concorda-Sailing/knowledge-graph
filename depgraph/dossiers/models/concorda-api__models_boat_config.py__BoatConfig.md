---
node_id: concorda-api::models/boat_config.py::BoatConfig
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4be81f2479bd7accb2e239c310bd7c5714e027ee9918032da1da68682b0aab08
status: current
---

# BoatConfig

## Purpose

Backend SQLAlchemy model for a boat's named position layout — Spinnaker, No-Spin, Delivery, Doublehanded, etc. Each boat owns multiple `BoatConfig` rows; one may be flagged `is_default`. `positions` is a free-form JSON list of `{name, location_x, location_y, count?}` objects describing where crew sit on a deck diagram. The model exists so that event/race planning can attach a specific config to a `SailingEvent` (via `boat_config_id`) and render the right slot count and labels without having to shape-match positions at read time. Future Claude editing this: this is the *source* table for "how many crew does this boat need today, and what are their roles?" — anything that downstream code keys off (slot counts, position names, presets) lives here.

## Invariants

- One `is_default=True` row per `boat_uuid` at most — `create_boat_config` and `update_boat_config` both demote any prior default in the same transaction when a new default is set.
- `boat_uuid` is a string FK-by-convention to `boats.id` (no SQL FK declared); always indexed and filtered by it on every read.
- `config_type` is a free string but expected to match a known preset family: `doublehanded`, `jib_main`, `spinnaker`, `full`. The web layer uses it to pick presets and icons.
- `positions` is JSON — never partially-mutated in place; always reassigned wholesale so SQLAlchemy's change-detection fires.
- `sort_order` is assigned at create time as `existing_count` (append-to-end). No code currently rebalances on delete.
- `id` comes from `BaseModel` (UUID); `type="BoatConfig"` is set in `__init__` for the polymorphic/audit envelope.

## Gotchas

- `SailingEvent` now stores `boat_config_id` directly (commit `bf15808 fix(schedule): use stored boat_config_id instead of shape-matching`). That means **deleting a BoatConfig can orphan event references** — the DELETE route does a hard `db.delete(config)` with no cascade or null-out, and there is no check for events pointing at it. This is a latent bug; preserve or warn before deleting in any new flow.
- Renaming a config or reordering `positions` retroactively changes what historical events render, because they only store the FK, not a snapshot. Commit `b4d60c6 fix(schedule): count accepted invites vs live slot count, drop position-name gating` already had to back off name-based matching once.
- `is_default` default is `False` with `server_default="0"` — SQLite-style. Don't change to a boolean literal without a migration.
- `sort_order` uses `existing_count` at create time, which is *not* `max(sort_order)+1`. After deletes, sort_order has gaps and new rows can collide on order with existing ones. Tolerable today because the list is short and `ORDER BY sort_order, name` breaks ties, but don't rely on uniqueness.
- The doublehanded preset arrived with `74b26e5 Add boat crew configurations with position diagram support` and was extended in `8b9722a feat: structured Achievement, double-handed preset` — preset definitions live in the web layer (`boat-positions-config.tsx`), not here. The model accepts whatever JSON the client sends; there is no server-side schema validation of `positions` element shape.

## Cross-cutting concerns

- **Auth**: every route guards with `_require_boat_owner(boat_id, current_user, db)` — only the boat's owner (and presumably co-owners via that helper) can CRUD configs.
- **Event planning**: `SailingEvent.boat_config_id` references these rows; `EventCrewSlot`/event-crew assignment derives slot counts from the linked config's `positions` length. Touching this model ripples into schedule-card counts and the dashboard event-plan panel.
- **No audit trail, no websocket events, no rate limits** specific to this resource.
- **No migrations beyond table creation**; column shape has been stable since `74b26e5`.

## External consumers

None known. No mobile/Expo direct usage; the iOS app reads through the same `/api/profile/boats/{id}/configs` endpoints. No scheduled jobs or webhooks reference `boat_configs`.

## Open questions

- Should deleting a `BoatConfig` that is referenced by a future `SailingEvent` be blocked, soft-deleted, or cascade-null? Currently it silently breaks the reference.
- Should `positions` element shape (`name`, `location_x`, `location_y`, optional `count`) be enforced server-side via a Pydantic sub-model rather than `JSON`? Today the contract lives entirely in the web preset code.
- Is `config_type` worth promoting to an Enum, or is the loose string deliberately keeping room for org-specific config families?

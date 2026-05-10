---
node_id: concorda-api::schemas/profile.py::BoatRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2e3b7aca920e69f4e0716b2a7e871c783fdea22baecf1b927206bd825d301e1e
status: current
---

# BoatRead

## Purpose

Backend Pydantic read schema for boat objects returned by every boat-listing/detail endpoint. Mirrors the `Boat` model's persisted fields plus `picture_url` / `banner_url` and the legacy `owner_ids` array, and is the wire contract for `GET /api/profile/boats`, `POST /api/profile/boats`, `PUT /api/profile/boats/{id}`, and the four picture/banner upload+delete endpoints. Seven router dependents serialize through it, and the web `useBoats` hook plus `Boat[]` typed state on the iOS app implicitly trust this shape. If a field needs to surface in the UI, it must appear here — the routers do not assemble responses field-by-field, they `.from_orm` straight into `BoatRead`.

## Invariants

- `id`, `type`, `created`, `modified`, `sail_number` are **non-optional**; everything else is `Optional`. Don't add new required fields without a migration that backfills — `from_attributes=True` will explode on rows missing the value.
- Field set is the union of `Boat` model columns the public API exposes. New columns on the model do **not** automatically flow through; they must be added here too. Several model attributes (`address` JSON, `additional_data`) are deliberately omitted today — see Gotchas.
- `owner_ids` is included for legacy/compat reasons even though canonical ownership lives in `BoatCrew(role='owner', status='active')`. Consumers that derive owner identity from this list will silently miss co-owners added through the BoatCrew path. Per the Boat model dossier, **new code should not depend on this field** — it's read-only legacy.
- `positions` is `Optional[list[dict]]` with no Pydantic shape validation; downstream snapshots into `SailingEvent.positions_needed` per the model dossier.
- `Config.from_attributes = True` (Pydantic v2 successor to `orm_mode`); router code passes ORM `Boat` instances directly. Removing this breaks every dependent.

## Gotchas

- **Legacy flat location columns vs `address` JSON**: schema exposes `location_club`, `location_city`, `location_state`, `mooring_slip` — the legacy flat fields. The Boat model's newer `address` JSON dict is **not** in this schema. Reads from `BoatRead` see the flat columns only; writers (`BoatCreate`, `BoatUpdate`) only touch the flat columns; `address` JSON is dark to the API layer. Migration to `address` is incomplete.
- **`needs_handicap_help` defaults differ** across the three schemas in this file — `BoatCreate` defaults `False`, `BoatUpdate` defaults `None`, `BoatRead` defaults `False`. The read default masks NULL rows as `False`; if a frontend ever needs to distinguish "not set" from "explicitly false," this default hides it.
- **Computed/owner info caveat**: this schema does **not** carry resolved owner Person data — only the legacy `owner_ids: list[str]`. Consumers that want owner names join separately (e.g. crew detail endpoints, boat finder owner-display logic). Commit `7aae433` ("Add banner/picture URLs to boat finder, club affiliations to crew detail") added the URL passthroughs but **not** owner-name passthrough; that asymmetry still holds.
- **`meta` is read-back asymmetric with create/update**: `BoatCreate` accepts `meta`, `BoatUpdate` accepts `meta`, `BoatRead` returns `meta` — but per the createBoat dossier, `meta` is write-once because it's not in the router's `BOAT_ALLOWED_FIELDS` update allowlist. Read consumers may see a `meta` value that no UI surface can edit.
- **No `boat_crew` / co-ownership info on the read shape**. Consumers needing co-owner lists hit `boatApi.getCrew` separately. Don't be tempted to inline crew here without checking the privacy contract on the boat-lookup info-leak path (see Boat model dossier).
- **`rating_ids: Optional[list[str]]`** is exposed but the rating system itself is sparse today; many rows return `None` or `[]`. Don't assume populated.

## Cross-cutting concerns

- **Auth**: this is a response schema, not gated itself; the dependent routers gate via `require_auth` plus `_require_boat_management` / `_require_boat_owner`. The schema is the same shape regardless of whether the caller is owner, co-owner, or admin — there's no field-level redaction here. If field-level privacy ever matters (e.g. `registration_number`), it must be enforced upstream in the router or with a separate `BoatReadPublic`.
- **Websocket**: routers that mutate Boat publish `BOAT_UPDATED`; the web `useBoats` hook assumes the post-event refetch returns this exact `BoatRead` shape. Any field rename here breaks the hook's typed cache silently if TypeScript types aren't regenerated in sync.
- **Audit**: no audit log entries are written by the dependent routers as of today (per createBoat dossier).
- **Side effects on other features**: every "my boats" UI path, the crew finder's self-exclusion filter, the event-create default-boat picker, the onboarding wizard step gating, and the iOS app boat list all consume this shape. A field removal cascades into all of them.

## External consumers

Concorda iOS Expo app (`reference_expo_app.md`) consumes the same shape via its own `ApiClient.getBoats` mirror — the JSON wire contract is effectively public to that app. The boat-finder and crew-finder pages render `picture_url` / `banner_url` directly into `<img>` tags; URL shape (relative `/uploads/...` vs absolute) must stay stable.

## Open questions

- When does `address` JSON become first-class on the read shape, letting the legacy flat location columns drop? Today reads must fall back through both shapes downstream.
- Should there be a `BoatReadPublic` (no `registration_number`, no `meta`, no `owner_ids`) for the boat-lookup / crew-finder peer-visible paths, vs. the current full-fidelity `BoatRead` for owner/admin views? Field-level privacy is currently enforced by route choice, not schema choice.
- Should `owner_ids` be removed from this schema once all consumers migrate to BoatCrew-derived ownership? Removing too early breaks any cached client; leaving it lets stale code keep computing wrong owner sets.

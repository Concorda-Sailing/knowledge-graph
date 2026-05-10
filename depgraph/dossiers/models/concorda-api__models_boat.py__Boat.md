---
node_id: concorda-api::models/boat.py::Boat
node_kind: model
feature: boats
last_reviewed: 2026-05-10
last_reviewed_against_hash: a4921747b957e2a8016d79fe825585bb011fcdb9003be8534ceec9438b84413e
status: current
---

# Boat

## Purpose

The boat entity. The center of gravity for crew, racing, and
ownership. A `Boat` row is the unit owners register, invite crew to,
configure positions for, share via co-ownership flows, and link to
sailing events.

Identity is `(sail_number, name)` after normalization (lowercase,
collapse whitespace, trim) per the boat-lookup convention. Sail
numbers alone are not unique across clubs — the name disambiguates.

## Invariants

- **`sail_number` is required**, name is optional but recommended.
  Boat-lookup matches both (when name is provided) per `docs/superpowers/specs/2026-04-14-coowner-request-flow-design.md`.
- **Ownership is via `BoatCrew` rows with `role='owner', status='active'`**,
  not via the legacy `owner_ids` JSON column. Multiple owners are
  allowed; they have equal authority. See
  `dossiers/ontology/role__relational__boat_owner.md` (in logigraph).
- **`positions` is a JSON list** (e.g. `[{"name": "skipper"},
  {"name": "main"}, {"name": "foredeck"}]`). Snapshotted into
  `SailingEvent.positions_needed` per-event so changing the boat's
  positions doesn't retroactively change past races.
- **`address` is a JSON dict** with shape `{club, city, state,
  mooring_slip}`. Replaces the legacy flat columns
  (`location_club`, `location_city`, etc.) but those are still
  populated for SQLite compat — migrate by reading from `address`
  with fallback to the legacy fields.
- **`additional_data` is freeform JSON.** Used for fields the
  canonical schema doesn't have yet. Treat as read-only unless you
  own the writing surface.

## Gotchas

- **Legacy columns are still present.** `owner_ids`, `picture_url`,
  `banner_url`, `location_club`, etc. are kept for SQLite compat with
  pre-migration rows. New code should NOT write to `owner_ids`
  (ownership is via BoatCrew); should write to `address` JSON for
  location, but old reads might still consult the flat columns.
- **`hard_cap` / `soft_cap`** are crew-size hints. `hard_cap` is the
  rule-enforced max (don't allow more accepted crew); `soft_cap` is
  the planning hint (warn but allow). Used by the roster service.
- **Boat-lookup info-leak prevention**: the public `/api/boats/lookup`
  endpoint returns no data when `exists=false`; when `exists=true`,
  returns only display name and owner names — not private boat
  metadata (registration_number, etc.). See
  `dossiers/.../crew_request_flow_design.md`. Don't add fields to the
  lookup response without checking the privacy contract.
- **`positions_needed` snapshot vs. live `positions`**: changing
  `Boat.positions` doesn't propagate to in-flight `SailingEvent` rows
  unless explicitly cascaded. The cascade was attempted in commit
  `31aa70d` and reverted in `d54327b` — the cascade orphan-cleanup
  was wrong. Currently positions changes do NOT cascade; treat
  `SailingEvent.positions_needed` as authoritative for that race.

## Cross-cutting concerns

- **Auth**: most boat-edit endpoints gate on `_require_owner`
  (`routers/boats.py:63`); read endpoints typically gate on
  `_require_crew_or_owner`. Crewfinder visibility (the
  `/crew/visible` endpoint) gates on
  `rule::crew_visibility::peer_pii_resume_gated`.
- **Co-owner flows**: promotion (crew → owner) requires unanimous
  approval via the `Approval` system; removal (owner → not-owner)
  requires mutual consent. See
  `docs/superpowers/specs/2026-04-14-coowner-request-flow-design.md`.
- **Crew lifecycle**: BoatCrew rows hold the membership; EventCrew
  rows hold per-event status. The boat-side roster persists across
  events.
- **Approvals reference boat by id**: deleting a boat with active
  approvals will orphan them. No cascade is wired — boats aren't
  deleted in practice (they're owned-out instead).

## External consumers

- **Concorda iOS app** consumes boat detail and crew list endpoints.
- Calendar feed inherits boat name through SailingEvent →
  Event → ICS rendering.

## Open questions

- **When does the legacy column purge happen?** `owner_ids`,
  `location_*`, `picture_url`, `banner_url`, etc. are dual-written
  in some places. Migration TBD.
- **`positions` shape standardization**: currently a list of dicts
  with at least `name`. Should there be a more structured shape
  (e.g. `{name, optional_role, capacity}`)? Not pressing.
- **Boat-class catalog**: `boat_class` is a free string. A
  controlled vocabulary would help with class-based race scoring,
  but isn't needed yet.

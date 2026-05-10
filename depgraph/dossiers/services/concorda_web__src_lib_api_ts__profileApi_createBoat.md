---
node_id: concorda-web::src/lib/api.ts::profileApi.createBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 177fa1a37ba01e7f9506ce09def9303a94901a306d4ef19b39ab245bb1cb04fb
status: current
---

# profileApi.createBoat

## Purpose
Client-side mirror for creating a brand-new `Boat` row — name, sail number, class, length, manufacturer, location, cap hints, optional initial `positions[]`. POSTs `BoatCreate` to `/api/profile/boats`; the backend persists the boat and seeds a `BoatCrew` row with `role="owner", status="active"` for the caller in the same transaction, so the caller automatically becomes an active owner. Returns the persisted `Boat` (id assigned, ready to drive boat-detail flows). This is the "register my J/24" / onboarding entry point — distinct from `profileApi.createBoatConfig` (line 1357), which adds a named position layout to a boat that already exists.

## Invariants
- Caller must hold a `PersonProduct` whose `TemporalProduct.grants_boat_management = True` — `_require_boat_management` 403s otherwise. Free/crew-only members cannot register boats.
- `sail_number` is required; backend rejects with 409 if any existing `Boat.sail_number` matches (case-sensitive, raw equality — see Gotchas). Other fields all optional.
- On success, exactly one `BoatCrew(role="owner", status="active")` row is seeded for `current_user.id` — ownership of new boats is always via `BoatCrew`, never the legacy `owner_ids` JSON column.
- Server emits `BOAT_UPDATED` over the websocket bus after commit; subscribers get the new boat id.
- Returns 201 with the populated `BoatRead` (including server-assigned `id`); the dialog/wizard flows rely on that `id` for the next step.

## Gotchas
- 409 sail-number collision is **global**, not scoped to club or owner. Per Boat model dossier, identity is really `(sail_number, name)` after normalization, but `create_boat` only checks raw `sail_number`. A second J/24 with the same sail number anywhere in the system blocks registration — the canonical lookup-uniqueness rule is not enforced on create. Worth surfacing in error UX.
- Easy to confuse with `profileApi.createBoatConfig` — different endpoint, different prereq, different intent. `createBoat` makes a Boat and seeds owner. `createBoatConfig` adds a position-set to an already-owned boat and is gated on `_require_boat_owner`. They share the word "create" and both touch `positions`-shaped data, so check the call site before edits.
- `BoatCreate` accepts `positions: list[dict]` and stores it directly; there's no Pydantic validation of the shape, and `SailingEvent.positions_needed` is snapshotted off this at event-create time (see Boat dossier on the snapshot vs. live divergence and the reverted `31aa70d` cascade attempt).
- `BoatCreate` still uses the legacy flat columns (`location_club`, `location_city`, `location_state`, `mooring_slip`) — the newer `address` JSON dict shape on the Boat model is **not** populated by this endpoint. Code reading boat location must fall back through both shapes.
- `60821ed` ("co-owner request path in add-boat form") and `bb9b274` ("3-col boat row, skip-later, sail-number lookup") split the add-boat UX: when sail-number lookup finds an existing boat, the form pivots to a co-owner request flow instead of calling `createBoat`. Don't change the createBoat path without checking the lookup-then-branch logic in `boat-dialog.tsx` / `setup/page.tsx`.
- `meta` field exists on `BoatCreate` but is not in the model's `BOAT_ALLOWED_FIELDS` update set — it is accepted on create but cannot be updated afterward through `updateBoat`. Likely an oversight.

## Cross-cutting concerns
- **Auth / entitlement**: `require_auth` + `_require_boat_management` (membership-gated, not just authenticated). Free signups cannot reach this even if logged in.
- **Side effect**: writes a `BoatCrew` row in the same transaction; downstream crew/roster queries immediately see the caller as owner.
- **Websocket**: `broadcast_event(BOAT_UPDATED, boat.id)` fires post-commit — fleet/admin views listening on the boat channel will refresh.
- **No audit log row** is written for boat creation today.
- **Onboarding wizard coupling**: `setup/page.tsx` chains `createBoat` → store `boat_uuid` → optionally `createBoatConfig` → optionally crew invites; failures mid-chain leave a partial state with no rollback.

## External consumers
Three direct dependents inside concorda-web — `app/members/setup/page.tsx::SetupPage` (onboarding wizard step), `components/profile/boat-dialog.tsx::BoatDialog` (modal add-boat), and `components/profile/boat-form-inline.tsx::BoatFormInline` (boats-tab inline add). Concorda iOS app is not currently observed to call this endpoint (boat creation appears to be web-only). No scheduled jobs or webhooks.

## Open questions
- Should sail-number collision be scoped (per club, per fleet) rather than global, to match the `(sail_number, name)` identity convention used by lookup? Today create is stricter than lookup uniqueness implies.
- Should `meta` be part of the updatable allowlist on `updateBoat`, or removed from `BoatCreate`? Current asymmetry means `meta` is write-once on creation only.
- Should the create flow also write `address` JSON (not just the legacy flat location columns) so reads can drop the fallback path?
- No cap on boats-per-owner; with `grants_boat_management`-gated membership that's probably fine, but worth confirming for spam-prevention if invite-based memberships ever expand.

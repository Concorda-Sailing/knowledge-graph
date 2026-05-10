---
node_id: concorda-web::src/lib/api.ts::profileApi.updateBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 212f0ad034d74a1db4b3c80344ded92674fff9ff5e031001ec97d4b344a7a046
status: current
---

# profileApi.updateBoat

## Purpose

Client-side mirror for owner-side boat field edits — name, sail number, class, location, photos. `PUT /api/profile/boats/{id}` returning the updated `Boat`. This is the single entry point for the "edit my boat" surface (8 components consume it: setup wizard, inline forms, dialog, info panel, two setup-page touch points, etc.). It exists to centralize the request shape and auth-required wrapper so callers never hand-roll the URL or forget the `BoatUpdate` typing. Future Claude editing this should preserve the thin-wrapper character — business rules belong on the server.

## Invariants

- HTTP verb is `PUT`; the body is `BoatUpdate` (TS type) which mirrors `routers/profile.py`'s `BOAT_ALLOWED_FIELDS` allowlist. Anything outside that allowlist is silently dropped server-side — don't rely on extra fields surviving.
- Returns `Boat` (the canonical read shape), not a `{message}` envelope. Consumers can swap their cached row directly.
- Uses `fetchApiAuthenticated` — token refresh + 401 surfacing handled by the shared client.
- `id` is the boat UUID string (matches `Boat.id`); not the sail number.
- Picture/banner uploads go through dedicated endpoints (`POST /boats/{id}/picture`, `POST /boats/{id}/banner`), NOT through this updater. Despite the dossier framing of "photos," `picture_url` / `banner_url` are not in `BOAT_ALLOWED_FIELDS`.

## Gotchas

- **`address` JSON migration story is not yet reflected here.** Backend allowlist still names the legacy flat columns (`location_club`, `location_city`, `location_state`, `mooring_slip`) — there is no `address` key. So the client sends flats; the model layer's `address` JSON dict is currently a read-side convenience populated elsewhere. If you add `address` to `BoatUpdate`, you must also extend `BOAT_ALLOWED_FIELDS` and reconcile dual-write semantics with the Boat dossier's "migrate by reading from address with fallback" rule.
- **`positions` is a JSON list** and IS in the allowlist — sending it overwrites the boat's position template wholesale. It does NOT cascade to in-flight `SailingEvent.positions_needed` (cascade was tried in `31aa70d`, reverted in `d54327b`). Past races keep their snapshot.
- **Owner-only.** Server returns 403 if `_owner_query` finds no active-owner `BoatCrew` row for the caller. Crew without owner role get 403, not 401 — surface this distinctly in the UI; recent co-owner work (`47688ac`, `eb382d2`) makes the active-owner gate user-visible.
- `model_dump(exclude_unset=True)` means undefined fields are not written, but explicit `null` IS written (and intersects the allowlist filter). Sending `{"name": null}` blanks the name.

## Cross-cutting concerns

- **Auth gate**: must be an active-owner `BoatCrew` row (`role='owner', status='active'`); legacy `owner_ids` JSON is NOT consulted. Co-owners have equal authority — any owner can edit.
- **Websocket**: success path emits `BOAT_UPDATED` on `boat.id` via `broadcast_event`. Subscribers (boat detail panels, dashboard, schedule cards) refetch on this. The delete-as-co-owner path also emits `BOAT_UPDATED` (not `BOAT_DELETED`) since the boat persists; sole-owner delete emits `BOAT_DELETED`.
- **No audit row** — boat edits are not logged today. Approvals/transfers have their own trail; bare field edits don't.
- **No rate limit** beyond the global authenticated bucket.
- **Hard cap / soft cap edits** ripple into roster service warnings but don't retro-trim accepted crew.

## External consumers

- Concorda iOS (Expo) app — consumes `Boat` reads and uses an analogous mutation; verify shape parity if `BoatUpdate` changes.
- None of: scheduled jobs, webhooks, public APIs.

## Open questions

- When does `BoatUpdate` (and `BOAT_ALLOWED_FIELDS`) gain `address` as a structured object, retiring the four flat location keys? Tracked obliquely in the Boat model dossier's "legacy column purge" question.
- Should a co-owner editing trigger a notification to other owners (silent edits today)? Not requested, but the directory-first co-owner UX work suggests visibility may matter.

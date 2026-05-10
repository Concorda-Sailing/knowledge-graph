---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteBoatPicture
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4b6ff8473cda0ef9c05a456c6538ccd836b8acc668d98c036e763875481eb8ff
status: current
---

# profileApi.deleteBoatPicture

## Purpose
Client-side mirror for an owner removing a boat's profile picture. Mirror endpoint of `uploadBoatPicture` — issues `DELETE /api/profile/boats/{boatId}/picture`, which sets `Boat.picture_url` to `null` and removes the underlying media file via `delete_upload("boats", boat.id)`. Returns the refreshed `Boat` so the caller can reconcile local state without a follow-up GET. Four components consume it: `BoatInline`, `BoatOwnerView`, `BoatDialog`, and `BoatFormInline` — all owner-facing edit surfaces.

## Invariants
- Path shape stays `/api/profile/boats/{boatId}/picture` and is symmetric with `uploadBoatPicture` (POST same URL). Both must move together.
- Returns full `Boat` (not `{message}`), matching the upload variant. Callers replace their local boat object with the response.
- Backend requires the caller be a boat owner (per `_owner_query`); a 403 here is expected for non-owners and should not be retried.
- File deletion is unconditional on the server side — `delete_upload` runs even if there was no picture set. The endpoint is idempotent from the client's perspective.
- Backend broadcasts `BOAT_UPDATED` over the websocket bus on success; consumers that subscribe to that event will re-render without needing the response payload.

## Gotchas
- The handler deletes the file *before* clearing `picture_url`. If `delete_upload` ever raises, the row keeps a stale URL pointing at a missing file — no transaction wraps the two. No reports of this biting yet, but worth knowing during refactors.
- `delete_upload("boats", boat.id)` removes the entire boat's picture directory by id — it is not URL-aware. Sharing storage between picture and other boat assets in that bucket would cause collateral deletion.
- Mirror parity with `deleteBoatBanner` is load-bearing: components like `BoatFormInline` and `BoatDialog` call the picture and banner deletes through identical patterns. Diverging signatures will silently drift the UI.
- No recent commits touch this function directly; the surrounding `profileApi` block has been stable. Don't assume "no changes = safe to refactor" — the four consumers all hard-code the response shape.

## Cross-cutting concerns
- Auth: `require_auth` + boat-owner check on the backend. No client-side gate; components rely on already being in an owner-only view.
- Websocket: server emits `BOAT_UPDATED` for `boat.id`. Any list/detail view subscribed to that channel will refresh.
- Side effects: deletes a file from disk (irreversible). No audit log entry — picture removal is not currently tracked.
- Rate limits: none specific; falls under the global authenticated-route limiter.

## External consumers
None known. No mobile/Expo bindings, no scheduled jobs, no webhooks. Internal web app only.

## Open questions
- Should the file-delete + DB-clear be transactional (or at least clear-then-delete) so a storage failure doesn't strand a broken `picture_url`?
- Worth emitting an audit/activity entry for picture removal, or is it too low-signal?

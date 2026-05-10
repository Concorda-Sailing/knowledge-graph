---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteBoatBanner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 80651e1d04da996505e631e252b8e4b50d4f3d609b497020d1f2528ea55d9750
status: current
---

# profileApi.deleteBoatBanner

## Purpose
Client-side mirror for an owner removing a boat's banner image. Mirror of `uploadBoatBanner`. DELETE `/api/profile/boats/{boatId}/banner` — backend authorizes via `_owner_query`, calls `delete_upload("boat-banners", boat.id)` to drop the media file, sets `Boat.banner_url = None`, commits, and broadcasts `BOAT_UPDATED`. Returns the refreshed `Boat`. Three components consume: `BoatInline` (inline editor), `BoatOwnerView` (owner profile detail), and `BoatSetupWizard` (initial boat onboarding) — all owner-facing surfaces where the wide banner image is editable.

## Invariants
- HTTP verb is DELETE; path matches `uploadBoatBanner` exactly (`/api/profile/boats/${boatId}/banner`).
- Resolves to `Boat` so callers can replace local state with the server's truth (`banner_url: null`) without an extra refetch.
- Uses `fetchApiAuthenticated` — owner-only operation, never callable anonymously.
- Storage subdir is `boat-banners` (distinct from `boats` used by `deleteBoatPicture`); the two image slots are independent.

## Gotchas
- Easy copy-paste error: `deleteBoatPicture` uses subdir `boats`, `deleteBoatBanner` uses `boat-banners`. If you refactor either, do not collapse them — banner and picture are stored in separate directories on disk and clearing the wrong one is silent (file simply isn't there).
- Banner and picture are independent fields on `Boat`. Deleting one must not touch the other; the backend handler is careful to only null `banner_url`. Don't add convenience "clear all images" logic here without an explicit product call.
- Backend broadcasts `BOAT_UPDATED` post-commit; consumers relying on websocket-driven cache invalidation should expect the same event for picture and banner deletes — not distinguishable from the event payload alone.
- Recent commits in this file are crew/schedule/co-owner work; banner endpoints have been quiet, so behavior here is settled but lightly exercised — be cautious about adding surprises.

## Cross-cutting concerns
- **Auth**: `require_auth` + `_owner_query` — must be a current owner (not just past). Co-owner relationship is honored via the same query used by other boat-mutation endpoints.
- **Side effects**: filesystem `delete_upload` is best-effort (does not raise if the file is missing); DB write to `Boat.banner_url`; websocket `BOAT_UPDATED` broadcast.
- **Audit**: no explicit audit-log entry beyond the broadcast event.
- **Rate limits**: none specific to this endpoint.

## External consumers
None known. Web-only; the Expo iOS app does not currently expose banner editing.

## Open questions
- Should banner deletion be undoable / soft-deleted? Currently the file is removed from disk immediately on click; there is no "restore" path if a user mis-clicks in the wizard. Not flagged as a problem yet, but worth considering when the boat-media UX is next revisited.

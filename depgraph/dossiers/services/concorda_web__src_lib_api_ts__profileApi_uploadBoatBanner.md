---
node_id: concorda-web::src/lib/api.ts::profileApi.uploadBoatBanner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2a5499b329f0d3c70903731b9c57be606c9682481a3e276e2d9d80d7305d01bd
status: llm_drafted
---

# profileApi.uploadBoatBanner

## Purpose

Client-side mirror for an owner uploading a banner (header) image for one of their boats. Wraps `fetchApiUpload` to POST a single `File` as `multipart/form-data` to `/api/profile/boats/{boatId}/banner`; the server re-encodes the image to JPEG and stores the resulting URL on `Boat.banner_url`, returned in the `Boat` response so the caller can rerender immediately. Parallel to `uploadBoatPicture` but with a wider/larger ceiling (1600px max edge vs. 512px) intended for the wide hero-strip rendered above the boat detail and on the boat-setup wizard. Three components consume it: `BoatInline` (boat-inline.tsx:213), `BoatOwnerView` (boat-owner-view.tsx:189), and `BoatSetupWizard` (boat-setup-wizard.tsx:198) — all owner-facing edit surfaces.

## Invariants

- Endpoint is POST `/api/profile/boats/{boatId}/banner` with body field name `file` — `fetchApiUpload` hard-codes `formData.append("file", file)`, must match the FastAPI `File(...)` param name.
- Auth is bearer-token via `Authorization` header; the server's `require_auth` rejects anonymous calls and the handler 403s if the caller isn't an owner of `boat_id` (per `_owner_query`). Co-owners with role=owner pass; viewers/managers/crew get 403.
- Response type is `Boat` (full record) — callers expect to reconcile local state from the returned object, not from a URL string.
- Server passes `max_dimension=1600` to `save_upload` (vs. the default 512 used by `uploadBoatPicture`). Don't "normalize" the two endpoints to share dimensions — banners are intentionally wider/higher-res because they're rendered as a full-bleed hero.
- File constraints (enforced server-side in `utils/image_utils.save_upload`):
  - MIME must be one of `image/jpeg`, `image/png`, `image/webp`, `image/gif` → otherwise 400.
  - Raw bytes must be ≤ 10 MB → otherwise 400.
  - Image is downscaled to max 1600px on the long edge and re-saved as JPEG q=85.
- Storage subdir is `boat-banners` (NOT `boats`) — the banner and picture for the same boat live in different directories and never collide. `deleteBoatBanner` must use the same `"boat-banners"` key.

## Gotchas

- All three current consumers render `boat.banner_url` directly via `<img src={boat.banner_url}>` without going through `authedUrl()`. This works today because the server returns the URL with a token query string baked into it (or because banner uploads are served from a path that doesn't require the auth header) — but if the upload endpoint ever changes to return a bare `/api/uploads/...` path the way `picture_url` does, all three banner renders will silently 401. Worth double-checking against the picture-render path before any change to `save_upload`'s URL output.
- `fetchApiUpload` does NOT set `Content-Type` manually — letting `fetch` derive the multipart boundary from `FormData`. Don't "fix" this by adding `Content-Type: multipart/form-data`; it will strip the boundary and the server will 422.
- No client-side pre-validation: a 12 MB iPhone HEIC will round-trip to the server before failing. HEIC is not in `ALLOWED_MIME_TYPES`, so iOS users on default settings hit a 400 with no inline guidance. The wizard surface (`BoatSetupWizard`) is the most user-facing of the three and the most likely place to add a pre-flight check first.
- 1600px JPEG q=85 produces files in the 200-500 KB range — fine for one-off renders but watch out if a future "boat directory grid" tries to load 50 banners at once. There is no thumbnail variant.
- Server-side `save_upload` runs through `ImageOps.exif_transpose` and forces RGB — EXIF-rotated phone photos display upright; CMYK/animated-GIF frames get flattened.
- No git fixes have landed against this specific function; surrounding `profile.py` boat endpoints have churned around co-owner invites (`47688ac`, `eb382d2`, `9e1cc53`), but the upload contract is stable.

## Cross-cutting concerns

- **Auth:** bearer token via `localStorage.auth_token`; SSR callers will hit `Not authenticated`.
- **Authorization:** owner-only via `_owner_query`. Same gate as `uploadBoatPicture`.
- **Realtime:** server emits `BOAT_UPDATED` via `broadcast_event(BOAT_UPDATED, boat.id)` after commit — any subscribed component (boat list, directory, the other two banner-edit surfaces if open in another tab) will refresh independently.
- **Side effects:** writes to disk under `PHOTOS_DIR/{boat.id}/boat-banners/`, mutates `Boat.banner_url`, commits the row. Pairs with `deleteBoatBanner` which both unlinks the file and nulls the column.
- **Audit:** no audit-log entry written.
- **Rate limit:** none on this endpoint as of writing.

## External consumers

None known. Same-origin web app only. The Expo iOS app does not currently surface boat-banner editing. No webhooks or scheduled jobs read `banner_url`.

## Open questions

- The three consumers render `banner_url` raw (no `authedUrl`) while picture renders use `authedUrl` — is the URL format actually different between the two endpoints, or is one set of consumers wrong? Worth resolving before adding a fourth consumer.
- 1600px is generous — is there a measured bandwidth/perceptual-quality tradeoff, or is it just "bigger than picture, felt right"? If banners are ever rendered in a list/grid, a 800px variant would help.
- Should client validate size/MIME before POST? More valuable here than for `uploadBoatPicture` because banner files are typically larger and the wasted-bandwidth cost on a failed upload is higher.

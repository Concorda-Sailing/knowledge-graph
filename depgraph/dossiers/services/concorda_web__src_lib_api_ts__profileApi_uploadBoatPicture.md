---
node_id: concorda-web::src/lib/api.ts::profileApi.uploadBoatPicture
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fc9b61b84018fefb63b9d38d194fe1383386868a96d0576bf427a88af8b9626
status: current
---

# profileApi.uploadBoatPicture

## Purpose

Client-side mirror for an owner uploading a profile picture for one of their boats. Wraps `fetchApiUpload` to POST a single `File` as `multipart/form-data` to `/api/profile/boats/{boatId}/picture`; the server (re-)encodes the image to JPEG and stores the resulting URL on `Boat.picture_url`, returned in the `Boat` response so the caller can rerender immediately. Exists because the four boat-edit surfaces (`BoatInline`, `BoatOwnerView`, `BoatDialog`, `BoatFormInline`) all need a one-shot "user picked a file, persist it, swap the preview" call without reaching for `fetch` directly.

## Invariants

- Endpoint is POST `/api/profile/boats/{boatId}/picture` with body field name `file` — `fetchApiUpload` hard-codes `formData.append("file", file)`, must match the FastAPI `File(...)` param name.
- Auth is bearer-token via `Authorization` header; the server's `require_auth` rejects anonymous calls and the handler 403s if the caller isn't an owner of `boat_id` (per `_owner_query`).
- Response type is `Boat` (full boat record, not just the URL) — callers expect to update local state from the returned object.
- Returned `picture_url` is an `/api/uploads/photos/...?t=<unix>` path, NOT a full URL; it requires the `authedUrl()` helper to append `?token=` (or `&token=`) before being usable in an `<img src>`.
- File constraints (enforced server-side in `utils/image_utils.save_upload`):
  - MIME must be one of `image/jpeg`, `image/png`, `image/webp`, `image/gif` → otherwise 400.
  - Raw bytes must be ≤ 10 MB → otherwise 400.
  - Image is downscaled to max 512px on the long edge and re-saved as JPEG q=85; the original is not retained.
- Storage key is `(subdir="boats", entity_id=boat.id)` and writes the single canonical file `photos/{boat.id}/boats/image.jpg` (overwrites prior upload — no version history kept for boat pictures).

## Gotchas

- The `?t=<timestamp>` cache-buster on the returned URL is what makes the `<img>` actually refresh after a re-upload; if a caller caches the old URL string instead of using the response's new one, the new image won't appear.
- `authedUrl` is mandatory in browser `<img>` tags because `/api/uploads/...` is auth-gated — bare `picture_url` from the API response will 401 silently and render as a broken image.
- No client-side pre-validation: the `File` is sent as-is. A 10MB+ HEIC photo from an iPhone will round-trip to the server before failing with a 400. If the UX needs an inline error before upload, gate in the component, not here.
- `fetchApiUpload` does NOT set `Content-Type` manually — letting `fetch` derive the multipart boundary from `FormData`. Don't "fix" this by adding `Content-Type: multipart/form-data`; it will strip the boundary and the server will 422.
- Server-side `save_upload` runs through `ImageOps.exif_transpose` and forces RGB — uploads of EXIF-rotated phone photos display upright; CMYK/animated-GIF frames get flattened. Callers should not assume the byte-stream they sent is what other clients will fetch.
- No git fixes have landed against this specific function recently; the surrounding `profile.py` boat endpoints have churned around co-owner invites (`47688ac`, `eb382d2`, `9e1cc53`), but the upload contract is stable.

## Cross-cutting concerns

- **Auth:** bearer token via `localStorage.auth_token`; SSR callers will hit `Not authenticated`.
- **Authorization:** owner-only. Co-owners with role=owner pass; viewers/managers/crew get 403.
- **Realtime:** server emits `BOAT_UPDATED` via `broadcast_event(BOAT_UPDATED, boat.id)` after commit — any subscribed component (boat list, directory) will refresh independently of the calling component.
- **Side effects:** writes to disk under `PHOTOS_DIR`, mutates `Boat.picture_url`, commits the row. Pairs with `deleteBoatPicture` which both unlinks the file and nulls the column.
- **Audit:** none specific to picture upload (no audit-log entry written).
- **Rate limit:** none on this endpoint as of writing.

## External consumers

None known. Same-origin web app only; the Expo iOS app uses a different upload path. No webhooks or scheduled jobs read `picture_url`.

## Open questions

- Should client validate size/MIME before POST to avoid wasted bandwidth on obviously-bad files? Not currently a complaint, but trivially additive.
- HEIC (iOS default) is not in `ALLOWED_MIME_TYPES` — uploads silently fail for users who haven't toggled "Most Compatible" on their iPhone. Worth surfacing in the picker accept attribute or transcoding client-side.

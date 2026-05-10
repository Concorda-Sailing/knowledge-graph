---
node_id: concorda-api::utils/image_utils.py::save_upload
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ebe3f392e33002e1ff5eb4bc555be57ab535d39878ac6851e1da81774ed3a00
status: llm_drafted
---

# save_upload

## Purpose
The single image-upload pipeline shared by every entity that has a picture in Concorda — boats, persons, events, the org logo. Callers hand it a `UploadFile`, a category subdir (`picture`, `banner`, `logo`, etc.), and an entity id; it validates MIME, enforces a 10 MB cap, decodes through PIL, applies EXIF orientation, downscales to fit a `max_dimension` box (default 512), and writes a normalized JPEG q=85 under `photos/{entity_id}/{subdir}/`. Returns a `/api/uploads/photos/...?t=<unix>` URL — the `?t=` is the cache-buster the web/Expo clients rely on when they replace `<img src>` after upload. Centralizing here means new upload endpoints inherit the same validation, EXIF fix, and dimension policy for free; resist the urge to inline a one-off variant.

## Invariants
- Only `image/jpeg`, `image/png`, `image/webp`, `image/gif` accepted; reject with 400 before any disk I/O.
- 10 MB hard cap on the raw upload body.
- Output is always JPEG q=85, RGB, with EXIF orientation already baked in via `ImageOps.exif_transpose` — downstream code must never re-rotate.
- `max_dimension` is a *bounding box* (PIL `thumbnail`), not a forced square; aspect ratio is preserved.
- Single-image mode (`many=False`) overwrites `image.jpg` in place — the URL path is stable across uploads, only the `?t=` query changes.
- Many-image mode writes `{YYYY}/{MM}/{DD}/{HHMMSS}-{rand8}.jpg` and never overwrites; reserved for categories that retain history.
- Returned URL is always relative-rooted at `/api/uploads/photos/` and includes the cache-buster suffix.

## Gotchas
- The cache-buster is *load-bearing*. The web `profileApi.uploadBoatPicture` / `uploadBoatBanner` consumers stash the returned URL straight into state — without `?t=`, browsers serve the prior `image.jpg` from cache and "the upload didn't work" bugs surface.
- `file.file.read()` reads the whole body into memory before the size check — a malicious 10 GB upload still allocates 10 GB. The MIME pre-check helps but isn't a real guard; the real guard is the FastAPI/uvicorn body limit upstream.
- MIME comes from the client-declared `content_type`, not magic-byte sniffing despite the framing — PIL's `Image.open` is the actual format gate. A `.gif` renamed to `image/jpeg` will be rejected by PIL, not by the MIME check.
- `datetime.utcnow()` is naive — fine here because it only feeds `strftime` for path construction, but don't lift this pattern into model code (project convention is `UtcDateTime` + aware UTC).
- Caller is responsible for persisting the returned URL on the entity row; this function has no DB awareness.

## Cross-cutting concerns
- Auth: enforced by each calling route, not here. `save_upload` will happily write to any `entity_id` it's handed — never expose it to an unauthenticated path.
- Filesystem: writes under `PHOTOS_DIR` (see `database.PHOTOS_DIR`); on prod this is bind-mounted, on dev it's repo-local. Backup/retention lives at the volume level, not in app code.
- Companion `delete_upload` only handles single-image mode and prunes empty parent dirs — many-image categories have no built-in delete path.
- No websocket event, no audit log entry. If an upload should notify other clients (e.g. boat banner change), the route must emit it.

## External consumers
None directly — only internal route handlers. The returned URL shape (`/api/uploads/photos/...?t=...`) is consumed by the web app and Expo iOS app via `profileApi.*` and equivalent fetchers; changing the URL prefix or dropping the cache-buster is a breaking client change.

## Open questions
- Should we move to magic-byte sniffing + streamed size check to close the 10 GB allocation gap, or rely on a uvicorn/Caddy body limit?
- Many-image mode has no delete/prune story — is that intentional (audit trail) or an oversight waiting for the first "I uploaded the wrong one" ticket?

---
node_id: concorda-web::src/lib/api.ts::mediaApi.upload
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6f6eaf71fc2ccb46c48994d5f73389bfecea6b0de0ebe9030e3a1824c7f98d0c
status: llm_drafted
---

# mediaApi.upload

## Purpose
Client-side mirror for uploading a media file (NOR/SI PDFs, regatta result PDFs, boat documents, gallery photos). Builds a `multipart/form-data` POST to `/api/media/upload` with the binary in the `file` part and the categorization (`folder_uuid`, `entity_type`, `entity_uuid`, `document_type`, `scope`) as URL query params. Hand-rolls the `fetch` (rather than going through `fetchApiAuthenticated`) because `FormData` must not have its `Content-Type` overridden — the browser needs to set the multipart boundary itself. Three surfaces upload through here today: the admin file manager, per-boat documents, and per-boat photo galleries. Partner of `mediaApi.deleteFile` — anything uploaded here is destroyed there.

## Invariants
- Method is `POST`, path is `/api/media/upload` (singular `upload`, not `/files`).
- Binary goes in the `file` form part; everything else is a query-string param. Don't move categorization into the form body — the FastAPI handler reads them via `Query(...)`, not `Form(...)`.
- Auth is mandatory and bearer-token-only: throws `"Not authenticated"` synchronously if `getAuthToken()` returns null. Do not add a fallback header path or cookie auth here.
- Do NOT set `Content-Type` on the request — the browser computes the multipart boundary. Adding `application/json` or `multipart/form-data` by hand will break the upload server-side.
- File-size cap is **50 MB** (`MAX_FILE_SIZE` in `routers/media.py`). Enforced server-side; the client doesn't pre-check.
- MIME allowlist (server-side): `image/jpeg|png|webp|gif`, `application/pdf`, `application/msword`, `.docx`, `application/vnd.ms-excel`, `.xlsx`, `text/plain`, `text/csv`. **SVG is intentionally rejected** (inline-JS XSS via the `serve` endpoint).
- `owner_uuid` is **not** exposed by this client wrapper. Server defaults `owner_uuid` to `current_user.id`; only admins can override. There is no `boat_uuid` field — boat scoping uses `entity_type="boat"` + `entity_uuid=<boatId>`.
- Scope defaults to `"private"` server-side when omitted; valid values are `private | crew | public`.

## Gotchas
- **SHA-256 dedup → 409.** Server hashes contents and rejects re-upload of the same bytes for the same `(entity_type, entity_uuid, document_type)` triple with `409 "This file has already been uploaded"`. `boat-photos.tsx` specifically string-matches `"already been uploaded"` to count duplicates instead of erroring; if you reword that detail string, fix that caller in the same commit.
- **Image magic-byte check.** Server sniffs the first bytes of jpeg/png/gif/webp uploads and returns 400 `"File contents don't match declared type"` if the header doesn't match the declared MIME. A correctly-named PNG that's actually HTML will be rejected — this is a security feature, not a bug.
- **Error path is non-standard.** This wrapper bypasses `fetchApiAuthenticated`, so it doesn't go through the shared interceptor. It manually parses `body.detail` and throws `new Error(detail)`. Callers get a string, not a structured error — they can't distinguish 400 (bad MIME) from 409 (duplicate) from 413-equivalent (too large) from 403 (admin-on-behalf-of) without substring matching.
- `admin/files/page.tsx` uploads with **only** `scope: "private"` and no entity/folder; those files float free in the admin tray. Don't assume `entity_type`/`entity_uuid` are always present when reading back.
- The `owner_uuid` query param exists server-side but no caller passes it from this wrapper; if a future caller needs admin-on-behalf-of upload, add it to the params type rather than reaching past the wrapper.

## Cross-cutting concerns
- **Auth:** bearer token via `getAuthToken()`, attached as `Authorization: Bearer ...`. Server enforces `require_auth`.
- **Side effects:** writes bytes to `DOCUMENTS_DIR/media/<owner_uuid>/<file_uuid><ext>` AND inserts a `media_files` row. Stores `content_hash` in `file_metadata`. No event bus, no webhook, no audit log.
- **Disk before commit.** Server writes the file to disk *before* `db.commit()`. A commit failure leaves an orphan file on disk; nothing reaps it today.
- **Rate limiting:** general API limiter only; no per-route upload throttle. The single-worker constraint (see `auth.py` memo) means the whole API blocks while large uploads stream into memory — `file.file.read()` slurps the whole body into RAM before the size check.
- **No websocket broadcast.** Peers viewing the same gallery/document list don't see new files until they refetch (`fetchDocuments()` / `fetchPhotos()` / `load()` in the three callers).
- **Serve-time auth coupling.** Files uploaded with `scope: "crew"` are gated by `crewfinder.view`/`crewfinder.contact` permissions on read; uploading `scope: "public"` makes the file unauth-readable forever via `/api/media/serve/...`.

## External consumers
None known. Web-only. The Expo iOS app does not currently upload media. No scheduled jobs, no third-party integrations POST to `/api/media/upload`.

## Open questions
- Should the client pre-check size (50 MB) and MIME before POSTing, to avoid streaming a rejected 200 MB file across the wire?
- Should size-check happen via streaming on the server instead of `file.file.read()` into RAM? A handful of concurrent 50 MB uploads under a single uvicorn worker is a memory-pressure footgun.
- Should orphaned disk files (commit failed after `write_bytes`) be reaped by a janitor, or should the write move into the transaction via a 2-phase pattern?
- Should `document_type` be a typed enum on the client rather than a free-string param? Today callers pass `"photo"` / `uploadCategory` with no shared vocabulary.

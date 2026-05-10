---
node_id: concorda-web::src/lib/api.ts::mediaApi.deleteFile
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ba8bdb1eff6aedfeff2a28e0f24cc29f72eec35f31758f8a561b6848a6acdd0
status: llm_drafted
---

# mediaApi.deleteFile

## Purpose
Client-side mirror for deleting a media file (NOR/SI PDFs, regatta result PDFs, boat documents, gallery photos). Issues an auth-gated `DELETE /api/media/files/{id}` and resolves to `void` on 204. Exists so UI surfaces (admin file manager, per-boat documents, per-boat photo galleries) share one wire contract — every file-delete in the app funnels here, and the backend's `_can_manage_file` decides what actually goes through. A future Claude editing this should treat it as a thin transport: any policy or cleanup logic belongs server-side, not in this wrapper.

## Invariants
- Method is `DELETE`, path is `/api/media/files/{id}` (singular `files`, mirrors `getFile`/`updateFile`); folder deletes go to `mediaApi.deleteFolder` and a different route.
- Response type is `void` — backend returns 204 No Content, not the deleted row. Don't change to expect a body.
- Auth is mandatory: routed through `fetchApiAuthenticated`, which attaches the bearer token; an unauth'd call must throw, not silently no-op.
- Server-side authorization lives in `_can_manage_file` (system_admin / org_admin / `owner_uuid == user.id` / `uploaded_by_uuid == user.id`). The client must not pre-filter — surfaces should let the API answer 403.
- Backend `unlink()`s the file from `DOCUMENTS_DIR` *before* the DB delete; treat the operation as destructive and irreversible from the UI's perspective (no soft-delete today).

## Gotchas
- 403 is a real response here, not just 404 — non-owner non-admin users hitting a public/crew file get permission-denied. All three current callers swallow the error into a generic toast ("Failed to delete file" / "Delete failed"); they don't distinguish 403 from 404 from 500. If you tighten error handling, do it at the call sites, not by changing this wrapper's signature.
- No optimistic-update contract: `admin/files/page.tsx` filters local state on success, but `boat-documents.tsx` and `boat-photos.tsx` re-fetch via `fetchDocuments()` / `fetchPhotos()`. Don't assume a uniform pattern when refactoring callers.
- The sibling `serve_file` endpoint had an Incident 2026-05-06 around DB session lifetime during streaming; `delete_file` doesn't stream, but anything that adds post-delete fan-out (e.g. CDN purge, thumbnail GC) must not hold the session across IO.
- File enumeration was hardened (commit context around `list_files` `owner_uuid` gate) — don't reintroduce a "list then delete by id" admin flow that bypasses that gate for non-admins.

## Cross-cutting concerns
- Auth: bearer token via `fetchApiAuthenticated`; server enforces `require_auth` + `_can_manage_file`.
- Side effects: deletes the row in `media_files` AND removes the file from disk (`DOCUMENTS_DIR / file_path`). No event bus, no webhook, no audit log entry today.
- No rate limiting specific to this route (general API limiter applies; see `auth.py` single-worker constraint memo).
- No websocket broadcast — peers viewing the same gallery/document list won't see the deletion until they refetch.
- No referential cleanup for entities that may embed `media_file.id` (e.g. boat picture_url, regatta document references). Deleting a file referenced elsewhere will leave a dangling pointer; UI shows broken thumbnails.

## External consumers
None known. Web-only API. Expo iOS app does not currently delete media. No scheduled jobs, no third-party integrations call this route.

## Open questions
- Should delete be soft (tombstone + retention window) given the disk `unlink()` is irreversible and there's no audit trail?
- Should the server reject deletion when the file is referenced as a boat picture / regatta NOR / event banner, or auto-null those references?
- Should owners of a boat (vs. just `owner_uuid` of the file) be allowed to delete boat-scoped docs/photos uploaded by another member? Today only the uploader or file-owner or an admin can.

---
node_id: concorda-api::models/media.py::MediaFile
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 74f748c8270160af431cffc160a56694d1e69c406fe397e592193dbe5c365b81
status: current
---

# MediaFile

## Purpose

Backend SQLAlchemy model for any file uploaded into Concorda — NOR/SI PDFs, regatta flyers, gallery photos, boat insurance/Coast Guard docs, race results, profile media. Carries ownership (`owner_uuid`, `uploaded_by_uuid`, `entity_type`/`entity_uuid`), classification (`document_type`: nor, si, flyer, insurance, coast_guard_reg, tow_boat, photo, other), visibility (`scope`: private/crew/public), and physical layout (`file_path` under `data/uploads/media/`, public `file_url`, `file_type` MIME, `file_size` bytes, optional `file_metadata` JSON for extraction output and image dimensions). It is the single backing store the media router, NOR-extract pipeline, and the upload/list/delete client APIs all read and write — change anything here and 9 router endpoints are in scope.

## Invariants

- `name`, `file_path`, `file_url` are non-null on every row — the upload endpoint must persist all three or fail before commit; orphaned DB rows pointing at missing disk files (or vice versa) will surface as broken downloads in `GET /api/media/serve/{uuid}`.
- `scope` is non-null with a `server_default="private"` — never trust client input to set scope to "public" without an authorization check; the model defaults to the safest choice on purpose.
- `entity_type` is a free-text discriminator (`regatta`, `boat`, `person`, `organization`) paired with `entity_uuid`; queries that filter by entity must match both columns or they will leak files across entity types that happen to share UUIDs.
- `document_type` is also free-text — there is no enum, no DB constraint. Callers (NOR extractor, boat doc upload) write the canonical strings listed in the column comment; new categories should be added there, not invented ad hoc.
- `folder_uuid` references `MediaFolder` by UUID with no FK constraint enforced; deleting a folder must either cascade or null out files at the application layer (see `DELETE /api/media/folders/{uuid}` in routers/media.py:244).
- `file_metadata` is JSON and may be null; readers must `.get()` defensively rather than index.

## Gotchas

- `owner_uuid` and `scope` were added in commit `3fa5fef` after the initial media service shipped (`ae448cb`) — older rows written before that migration may have null `owner_uuid` and the implicit "private" default. List/serve endpoints need to handle null owner gracefully (treat as orgwide-private or system-owned, not as "anyone").
- There is no `content_hash` column on this model despite dedup being a natural use case — the `mediaApi.upload` dossier or the framing may suggest one exists; it does not. Dedup today is by `(owner_uuid, name, entity_uuid)` collision detection at the router layer, not by hash. If you add hashing, add the column + index together and backfill.
- `entity_type` overlaps with `MediaFolder.entity_type` but the allowed value sets differ slightly (folders allow `event`, files document `regatta`/`boat`/`person`/`organization`) — don't assume folder and file scoping share a vocabulary.
- `uploaded_by_uuid` (audit: who uploaded) and `owner_uuid` (authorization: who owns) are intentionally distinct. An admin uploading on behalf of a member sets `uploaded_by_uuid=admin` but `owner_uuid=member`. Confusing them collapses the audit trail.
- `file_url` is stored as an absolute-path-style public URL; rewriting the static-serve mount point requires a data migration, not just a config change.

## Cross-cutting concerns

- **Authorization**: `scope` is the only thing standing between a private NOR draft and the public internet. Every read path (`GET /api/media/files`, `GET /api/media/files/{uuid}`, `GET /api/media/serve/{uuid}`) must filter by viewer identity vs. `owner_uuid` + `scope`. Crew-scoped files require resolving the viewer's crew membership against the file's `entity_uuid` when `entity_type == "boat"` — this logic lives in the router, not the model.
- **NOR extraction**: `POST /api/nor/upload-and-extract` and `POST /api/nor/extract/{uuid}` write extracted fields into `file_metadata` JSON; downstream regatta-import code reads from there. Schema changes to that JSON blob are silent — no validator catches drift.
- **Disk side effects**: Deleting a `MediaFile` row without removing the underlying file under `data/uploads/media/` leaks disk; `DELETE /api/media/files/{uuid}` (routers/media.py:421) is the canonical path and handles both. Don't bulk-delete via raw SQL.
- **No websocket/audit emission** from the model itself — all eventing happens at the router layer.

## External consumers

- Concorda web frontend `mediaApi.upload`, `mediaApi.listFiles`, `mediaApi.deleteFile` (see those dossiers).
- NOR import pipeline (`routers/nor.py`) reads `file_path` and writes `file_metadata`.
- Static file server mounted at `data/uploads/media/` resolves `file_url` directly; bypassing the API skips scope checks — only public-scoped files should be reachable that way.
- No known scheduled jobs, webhooks, or third-party integrations.

## Open questions

- Should `document_type` become an enum or lookup table? Free-text has already let callers drift (e.g. `coast_guard_reg` vs. potential `cg_registration`) — the cost of a migration vs. ongoing typo risk is unresolved.
- Is content-hash dedup worth adding? Several router callers re-upload the same NOR PDF across regattas; a `content_hash` column would let the upload endpoint short-circuit, but no one has measured the duplication rate.
- `MediaFolder` has no enforced FK from `MediaFile.folder_uuid` — should it? Cascading deletes would simplify the folder-delete endpoint but risk orphaning files users expected to keep.

---
node_id: concorda-api::models/media.py::MediaFolder
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f50f131c17db512caedb55ea76d9564745953d082e89324569d1d2fd6c5b5622
status: current
---

# MediaFolder

## Purpose

Backend SQLAlchemy model for a media folder — the hierarchical organizer that `MediaFile` rows reference via `folder_uuid`. A folder carries its own ownership (`owner_uuid`/`owner_type`: person, organization, boat, regatta, system), an optional entity binding (`entity_type`/`entity_uuid` for albums attached to a regatta, event, or boat), a visibility `scope` (private/crew/public), and a self-referential `parent_uuid` for nesting. It exists so the media router can present users a Drive-style tree without forcing every file into a flat namespace, and so albums can be tied to a regatta or boat without duplicating files. Four router endpoints (`GET/POST/PUT/DELETE /api/media/folders`) read and write this model exclusively; touching the schema is in scope for all four plus the file-delete cascade check.

## Invariants

- `name` and `scope` are non-null; `scope` has `server_default="private"` — the safest visibility wins by default and the model never allows ambiguous visibility.
- `parent_uuid` is a UUID string with **no enforced FK** to another `media_folders` row; the application layer is responsible for cycle prevention and orphan handling.
- `owner_uuid` is nullable (system-owned folders are valid) but the create endpoint stamps it with `current_user.id` when the caller omits it — null owner in practice means "created before owner_uuid existed" (pre-`3fa5fef`).
- Delete is **gated by emptiness**: `DELETE /api/media/folders/{id}` refuses if any `MediaFile.folder_uuid == id` or any child `MediaFolder.parent_uuid == id` exists (routers/media.py:244-247). There is no cascade. Bypassing the endpoint with raw SQL will orphan files.
- `owner_type` and `entity_type` are free-text discriminators with no DB constraint — allowed values are documented in column comments only (`owner_type`: person/organization/boat/regatta/system; `entity_type`: regatta/event/boat).
- Folder `entity_type` allows `event`; `MediaFile.entity_type` does not — the two vocabularies are intentionally non-identical, so folders can group event-scoped files even though files themselves bind to regatta/boat/person/organization.

## Gotchas

- `is_hidden: Boolean` was replaced with `scope: String` in commit `3fa5fef` — old code paths or imported data assuming a boolean hide flag are wrong. The migration mapped hidden → "private" implicitly; folders created before that may have `scope="private"` purely as the column default, not as an explicit user choice.
- `entity_type`/`entity_uuid` were added later in `a88ee0d` ("media albums") — earlier folders have null entity binding and are effectively floating. List/album views must tolerate null entity columns, not assume every folder has one.
- The list endpoint (routers/media.py:164) shows non-admins **public + crew + owned** folders — "crew" scope is leaked broadly here without any actual crew-membership resolution (unlike `MediaFile` where crew scope ought to gate by boat membership). If a folder is marked `scope="crew"`, every authenticated user sees the folder's existence and name. Files inside it are still scope-checked separately. Fixing this requires deciding what "crew" means for a folder that may have no `entity_uuid`.
- `parent_uuid` cycles aren't checked anywhere — a malicious or buggy PUT could set folder A's parent to its own descendant. Tree walkers (none in the router today, but `mediaApi.listFolders` consumers in concorda-web) must defend.
- Folder delete checks subfolder/file counts but does **not** check inside subfolders recursively — if you somehow have a folder containing only empty subfolders, delete will refuse. The 400 "Folder is not empty" message is opaque about which side (subfolder vs. file) triggered.

## Cross-cutting concerns

- **Authorization**: ownership is per-folder via `owner_uuid`; admins (`system_admin`, `org_admin`) bypass on read/write/delete. Non-admins cannot create, update, or delete a folder they don't own, and cannot pass `owner_uuid` for someone else on create.
- **No FK to `MediaFile.folder_uuid`**: cascading semantics live in the delete endpoint, not the DB. A `MediaFile` whose `folder_uuid` points at a now-deleted folder would be an orphan reference — today this can't happen via the API, but a manual SQL delete would break it.
- **No FK to `parent_uuid`**: same story for subtree integrity.
- **No websocket / audit emission** from the model — eventing, if any, is router-layer.
- **Disk side effects**: none directly. The folder is purely a logical grouping; physical files under `data/uploads/media/` are keyed by `owner_uuid`, not by folder path.

## External consumers

- Concorda web frontend `mediaApi.listFolders`, `mediaApi.createFolder`, `mediaApi.updateFolder`, `mediaApi.deleteFolder` (see those dossiers).
- Indirectly, `mediaApi.listFiles` filters by `folder_uuid` — renames or deletes of folders are visible to file browsers.
- No known scheduled jobs, webhooks, or third-party integrations.

## Open questions

- What does `scope="crew"` mean for a folder with no `entity_uuid` or with `entity_type="regatta"`? The list endpoint currently treats crew-scope as broadly visible to all authenticated users, which is almost certainly wrong but no one has hit it as a complaint yet.
- Should `parent_uuid` and `MediaFile.folder_uuid` become real FKs with `ON DELETE` semantics? The empty-folder guard works but is brittle; a cascade rule would make bulk cleanup safer.
- Recursive delete (folder + everything under it) is not exposed — should it be? Users hitting the 400 today have to walk the tree manually from the web UI.

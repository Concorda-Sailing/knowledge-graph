---
node_id: concorda-api::utils/image_utils.py::delete_upload
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cddefab3cd0a255f919b7d3ff47ed5ad91e5213f74c4360ef878b01782f0c27a
status: current
---

# delete_upload

## Purpose
Shared utility for deleting an uploaded media file from disk by `(subdir, entity_id)`. Companion to `save_upload` for the single-image path layout (`photos/{entity_id}/{subdir}/image.jpg`) — the only layout for which a delete makes sense, since `many=True` versioned uploads accumulate dated files this helper does not touch. Idempotent: silently no-ops when the file or its parent dirs are already gone, so callers don't need to gate on "did this entity ever have a picture?". After unlinking, it prunes the now-empty `subdir` and `entity_id` directories so the photos tree doesn't grow a bushy graveyard of empty folders. Six DELETE endpoints across `routers/profile.py`, `routers/events.py`, and `routers/admin.py` rely on this single point of contact for filesystem cleanup; if you change its semantics, all six endpoints inherit the change.

## Invariants
- Path layout is fixed at `photos/{entity_id}/{subdir}/image.jpg` — must stay symmetric with `_single_image_path` and the single-image branch of `save_upload`.
- Idempotent and exception-safe by contract: callers (the six DELETE handlers) invoke it before clearing the corresponding DB column without try/except. It must never raise on "file not found."
- Pruning walks at most two levels up (`subdir` dir, then `entity_id` dir) and bails the moment a directory is non-empty or `rmdir` fails. It must never recurse beyond the entity dir — pruning into `UPLOAD_DIR` itself would be a bug.
- Operates on the single-image slot only. The `many=True` versioned tree (dated subfolders) is intentionally untouched; there is no bulk-delete counterpart yet.

## Gotchas
- Subdirs are conventions, not enums. `boats` vs `boat-banners`, `people` vs `people-banners`, `events`, `logo` — typos are silent (no file = nothing to do = success), so a misspelled subdir in a new endpoint will look like it works while leaving the real file orphaned. Cross-check against the matching `save_upload` call site.
- Logo deletion uses literal `entity_id="org"` (`routers/admin.py:1038`) because the org has no per-row id; the path becomes `photos/org/logo/image.jpg`. Don't "normalize" entity_id to a UUID — you'll break the org logo.
- Callers delete the file *before* clearing the DB column. If `unlink()` ever raised on a permission error, the row would keep a URL pointing at a missing file. Today this is masked by the `if path.exists()` guard, but a future change that drops the guard or adds a raising codepath would expose all six endpoints at once.
- The `OSError` catch covers the race where a concurrent process repopulates the directory between `iterdir()` and `rmdir()`. `break` (not `continue`) is correct: if the inner dir won't prune, the outer one definitely won't be empty either.
- Only one commit touches this file recently (`ef1c3bd` — relocation from root into `utils/`). No behavior changes; treat the current shape as settled.

## Cross-cutting concerns
- **Auth**: enforced by each calling endpoint (`require_auth` plus owner/admin checks); this helper has no auth of its own and trusts its arguments.
- **Side effects**: irreversible filesystem mutation. No backup, no soft-delete, no audit-log entry from this layer. Calling endpoints emit their own websocket events (e.g. `BOAT_UPDATED`); this helper emits none.
- **Concurrency**: not synchronized. Two simultaneous deletes for the same entity will both succeed — second `unlink` hits the `path.exists()` guard. Pruning is best-effort under contention (the `OSError` swallow).
- **Storage scope**: rooted at `UPLOAD_DIR` (= `PHOTOS_DIR` from `database`). If photo storage ever moves to object storage, this is one of the choke points that must be reimplemented.

## External consumers
None known. Pure internal helper — no Expo bindings, no scheduled jobs, no webhooks. The six DELETE endpoints listed in the dependent set are the entire surface area.

## Open questions
- Should this be transactional with the DB column clear (delete-then-commit, or commit-then-delete with a reconciliation sweep) so a storage failure can't strand a stale URL? Currently each caller handles the ordering itself, inconsistently.
- Is there value in a `delete_upload_many(subdir, entity_id)` for the versioned path, or is the absence of bulk-delete intentional product policy (keep historical uploads forever)?
- Should removal emit an audit/activity entry? Today only the calling endpoint's websocket broadcast hints that anything happened.

---
node_id: DELETE::/api/profile/sailing-resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 86f507cd7815eed7284722609c59a6cfafe1b6e99aeddf0a39edba3bc55893c6
status: llm_drafted
---

# DELETE /api/profile/sailing-resume

## Purpose

Deletes the current user's sailing resume from the database. This is used when a user wishes to remove their professional credentials or US/World Sailing identifiers from their profile. It is distinct from the upsert/update logic, as it completely removes the `SailingResume` record associated with the `current_user.id`.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a 404 Not Found** if no `SailingResume` record exists for the authenticated user.
- **Deletes exactly one record** matching the `person_id` of the `current_user`.
- **Emits a broadcast event** upon successful deletion to notify connected clients.

## Gotchas

- **Recent schema expansion:** Following `feat(sailing-resume): add US/World Sailing credential fields` (commit `f311f7a`), this endpoint now clears the expanded set of credential fields (including `preferred_oa_ids`) along with the base resume.
- **Dependency on `current_user.id`:** The deletion is strictly scoped to the authenticated user's ID; there is no mechanism in this endpoint to delete another user's resume.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth`.
- **Websocket**: Emits `SAILING_RESUME_DELETED` to notify the frontend to clear resume-related UI components.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Triggers a UI state update for any component listening to `SAILING_RESUME_DELETED`.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.deleteSailingResume`

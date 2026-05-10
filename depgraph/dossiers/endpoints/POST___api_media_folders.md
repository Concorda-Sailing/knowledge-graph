---
node_id: POST::/api/media/folders
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a1c31520eef939352f10c85f6b7885f3a0d7786e77de89eefe5954d1618aca88
status: llm_drafted
---

# POST /api/media/folders

## Purpose

Provides the endpoint for creating new media folders within the media management system. It allows for the organization of files into a hierarchical structure by defining a name, a parent folder, and an owner. This is distinct from the `PUT` endpoint which modifies existing folders; this endpoint is the primary way to build out the media directory tree.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a `FolderRead` object** upon successful creation.
- **Ownership restriction**: Only users with `system_admin` or `org_admin` roles can specify an `owner_uuid` different from their own ID.
- **Default scope is `"private"`** if no scope is provided in the request body.
- **`parent_uuid` is optional**, allowing for top-level root folders.

## Gotchas

- **IDOR Protection**: Per commit `c9a7c41`, strict role-based checks are required when assigning ownership. If a user attempts to create a folder for another user without being an admin, the API must raise a 403.
- **DB Session Management**: Per commit `3fee226`, ensure that any logic involving file responses or heavy media operations does not leave the DB session open, as this can cause leaks during streaming.
- **Scope Validation**: The `scope` field must be validated against `VALID_SCOPES` (as seen in the `update_folder` logic) to prevent invalid visibility states.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `require_auth`. Role-based logic (admin vs. user) dictates whether `owner_uuid` can be manipulated.
- **Audit**: N/A
- **Rate limit**: N/A
- **Side effects**: Creation of a folder is a prerequisite for organizing `MediaFile` uploads; empty folders are a requirement for the `delete_folder` logic (which fails if children exist).

## External consumers

- `concorda-web::src/lib/api.ts::mediaApi.createFolder`

## Open questions

- Should there be a validation step to ensure the `parent_uuid` actually belongs to the same organization/user hierarchy before creation to prevent cross-tenant folder nesting?

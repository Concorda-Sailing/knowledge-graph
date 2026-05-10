---
node_id: concorda-web::src/components/admin/import-users-dialog.tsx::ImportUsersDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2d8d0f413dd551cafcf1405a979f968a76553ec31120bef394828c59da190809
status: llm_drafted
---

# ImportUsersDialog

## Purpose

Provides a modal interface for administrators to bulk-import users via CSV. It handles file selection, provides a downloadable template for correct formatting, and manages the lifecycle of the upload (loading, error, and success states). It is distinct from `ClubDialog` as it specifically targets user-level data ingestion rather than organizational metadata.

## Invariants

- **Uses `adminApi.importUsers`** — the primary side effect is a call to the admin-level API endpoint.
- **`onDuplicate` mode is required** — the user must choose between `"skip"` (default) or `"update"` to define behavior for existing email addresses.
- **Input is a `File` object** — the API expects a raw file-based upload.
- **`onSuccess` trigger** — the callback is fired only if `res.created > 0` or `res.updated > 0`.

## Gotchas

- **Mobile layout constraints** — per commit `0564f06`, the dialog is constrained with `sm:max-w-md` and must handle footer stacking on small screens to prevent UI breakage in the admin mobile view.
- **Template format** — the `downloadTemplate` function generates a hardcoded CSV string. If the API schema for `membership_types` or other fields changes, this template will become out of sync and cause import failures.

## Cross-cutting concerns

- **Auth**: Requires admin-level permissions via `adminApi`.
- **Audit**: N/A.
- **Side effects**: Successful imports will likely require a refresh of the user list in the parent `AdminListPage`.

## External consumers

None known.

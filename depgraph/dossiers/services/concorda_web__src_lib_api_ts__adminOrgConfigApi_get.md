---
node_id: concorda-web::src/lib/api.ts::adminOrgConfigApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ee6bedb98664ce8212f2a10f7a278d52513fd3683876edc5d402699237e65b5a
status: current
---

# adminOrgConfigApi.get

## Purpose

Provides access to the organization's global configuration and branding assets. It is used to retrieve the current `OrgConfigData` and to perform administrative updates such as changing configuration values or updating the organization's logo. This is the primary interface for the system administration settings page.

## Invariants

- **Requires authentication** — All methods (`get`, `update`, `uploadLogo`, `deleteLogo`) call `fetchApiAuthenticated`.
- **Returns `OrgConfigData`** — The `get` and `update` methods return the full configuration object, ensuring the UI has the latest state after a mutation.
- **`uploadLogo` uses multipart/form-data** — The `uploadLogo` method wraps a `File` object into a `FormData` instance via `fetchApiUpload`.
- **`update` uses `PUT`** — The `update` method performs a partial update of the configuration via a `PUT` request.

## Gotchas

- **Logo deletion is a destructive side effect** — Calling `deleteLogo` removes the existing asset from the server; ensure the UI provides a clear confirmation before triggering this via the `adminOrgConfigApi`.

## Cross-cutting concerns

- **Auth**: Requires a valid session via `fetchApiAuthenticated`.
- **Side effects**: Updates to this API affect the visual branding (logo) and configuration-aware logic across the platform.

## External consumers

- `AdminSystemPage` in `src/app/members/admin/system/page.tsx`.

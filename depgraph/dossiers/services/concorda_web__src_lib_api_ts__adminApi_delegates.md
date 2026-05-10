---
node_id: concorda-web::src/lib/api.ts::adminApi.delegates
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4126e355ed494ec92eb45164642ad8618302dcf89e689dea43ce547713c39b24
status: current
---

# adminApi.delegates

## Purpose

Fetches the list of organization delegates. It is a specialized endpoint within the `adminApi` object used to retrieve high-level administrative roles. Use this specifically for the `AdminDelegatesPage` to populate the administrative oversight view.

## Invariants

- **Returns a Promise of `DelegateInfo[]`**.
- **Uses `fetchApiAuthenticated`** to ensure the request includes the necessary bearer token.
- **Endpoint is `/api/admin/delegates`**.

## Gotchas

- **Admin-only access required.** Because this relies on `fetchApiAuthenticated`, the caller must have an active session with administrative privileges; otherwise, the request will fail at the network layer.
- **Directly consumed by `AdminDelegatesPage`**. Any changes to the return shape of this method will immediately break the rendering of the admin-side delegate management UI.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: N/A.

## External consumers

- `concorda-web::src/app/members/admin/delegates/page.tsx` (AdminDelegatesPage)

---
node_id: concorda-web::src/lib/api.ts::adminMerchandiseApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 11e35fd7ff2f4fde81db0e301305b38cc39b4ca4bd6c2585580e15740ed300ba
status: llm_drafted
---

# adminMerchandiseApi.delete

## Purpose

The method handles the deletion of a specific merchandise item from the administrative backend. It targets the `/api/merchandise/{id}` endpoint using a `DELETE` method. It is a specialized part of the `adminMerchandiseApi` service used to remove inventory or product entries.

## Invariants

- **HTTP Method is `DELETE`** — strictly follows the RESTful pattern for resource removal.
- **Returns `void`** — the function expects no body in the response; successful deletion is indicated by a 2xx status.
- **Requires `id`** — the target resource must be identified by a unique string.
- **Uses `fetchApiAuthenticated`** — the request must include valid authentication headers to succeed.

## Gotchas

- **No recent history of reverts or failures** — unlike the `schedule` or `events` modules which show frequent fixes for coupling or data shape (e.g., `b4d60c6` or `bf15808`), this specific endpoint has not been a source of recent regression in the provided history.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has administrative privileges.
- **Side effects**: Deleting a merchandise item will affect the visibility of that item in the `MerchandisePage` (the primary consumer).

## External consumers

- `concorda-web::src/app/members/admin/products/merchandise/page.tsx::MerchandisePage`

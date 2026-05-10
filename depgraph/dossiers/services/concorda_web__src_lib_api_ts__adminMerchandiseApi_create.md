---
node_id: concorda-web::src/lib/api.ts::adminMerchandiseApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 97a333c234889030af5433591b66f3627e319ee38f3ad47084a08c24b421f442
status: llm_drafted
---

# adminMerchandiseApi.create

## Purpose

Provides the API interface for creating new merchandise items within the administrative dashboard. It wraps a `POST` request to the `/api/merchandise` endpoint, accepting a `MerchandiseCreate` object and returning the newly created `Merchandise` instance. This is a specialized administrative tool used to expand the catalog of available products for the organization.

## Invariants

- **Method is `POST`** — strictly used for creation.
- **Uses `fetchApiAuthenticated`** — requires a valid administrative session/token to execute.
- **Input is `MerchandiseCreate`** — the payload must match the specific creation schema (which may differ from the full `Merchandise` type).
- **Returns `Merchandise`** — the response body is the full, persisted object including its generated `id`.

## Gotchas

- **Administrative context required** — because this uses `fetchApiAuthenticated`, the caller must have an active admin session; standard user tokens will result in a 401 or 403.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: Successful creation updates the product catalog, which is visible on the `MerchandisePage` (see `concorda-web::src/app/members/admin/products/merchandise/page.tsx`).

## External consumers

- `concorda-web::src/app/members/admin/products/merchandise/page.tsx` (MerchandisePage)

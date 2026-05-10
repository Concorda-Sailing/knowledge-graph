---
node_id: concorda-web::src/lib/api.ts::adminProductsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d9548702ee02ad6b3065143f52487d34fb8efd8e58f9df63d821b1fe9f93ec04
status: llm_drafted
---

# adminProductsApi.list

## Purpose

Fetches a list of products (Memberships or Events) from the admin backend. It is used to populate administrative views where products need to be filtered by a specific event. Use this when you need to list products that are contextually tied to an `event_id`.

## Invariants

- **Returns a `Promise<Product[]>`** via the `fetchApiAuthenticated` wrapper.
- **Supports optional filtering** via `event_id` (to scope products to a specific event) and `include_inactive` (to toggle visibility of disabled products).
- **Uses `GET` method** on the `/api/products` endpoint.
- **Requires authentication** via the `fetchApiAuthenticated` helper.

## Gotchas

- **Implicitly filters by event if `event_id` is provided.** If an agent attempts to use this for a global product list without passing the param, it may return an empty set or a restricted set depending on the backend's default behavior for un-scoped requests.
- **Dependency on `fetchApiAuthenticated`**. If the authentication layer is modified, this method's ability to retrieve the product list will break.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the caller has administrative privileges.
- **Side effects**: Used by `EventDetailContent` in `app/members/admin/events/[id]/page.tsx` to render product-related data within an event context.

## External consumers

None known.

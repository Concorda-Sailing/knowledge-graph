---
node_id: concorda-web::src/lib/api.ts::adminProductsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 87fb731ec6efa911db21e9bfc19da83e261948ec78cbcca400b72d2b19f255a0
status: current
---

# adminProductsApi.create

## Purpose

Creates a new product (Membership or Event-based) via the admin API. This method is the entry point for adding new revenue or registration streams to the platform. It is distinct from `eventsApi` methods, as it handles the creation of the product entity itself rather than the event-specific scheduling or crew assignments.

## Invariants

- **HTTP Method is `POST`** to `/api/products`.
- **Requires `fetchApiAuthenticated`** to establish the admin session.
- **Input must satisfy `ProductCreate`** (specifically requiring `name`, `slug`, and `price`).
- **Returns a `Product` object** upon successful creation.

## Gotchas

- **Requires `ProductCategory` alignment.** The `category` field must be one of the strictly typed values `"Membership"` or `"Event"` (see `PRODUCT_CATEGORIES` in `api.ts`).
- **Slug uniqueness.** While not explicitly guarded in the frontend type, the `slug` is a required part of the `ProductCreate` interface and is used for URL routing; duplicate slugs will likely cause a backend error.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` — requires an active admin session.
- **Side effects**: Successful creation of a product may impact the visibility of registration options on the `EventDetailContent` page (see `page.tsx:474` and `page.tsx:683`).

## External consumers

None known.

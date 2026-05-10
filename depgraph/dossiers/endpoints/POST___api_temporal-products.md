---
node_id: POST::/api/temporal-products
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7c0497fec9bc1aee755c8bba77b7873623c60fd39f6f5c944c524b8e033a656f
status: llm_drafted
---

# POST /api/temporal-products

## Purpose

Creates a new `TemporalProduct` instance, which serves as a container for seasonal merchandise (e.g., a specific year's branded gear). This endpoint is used by administrators to define the temporal boundaries (year and date range) and the associated merchandise for a specific season.

## Invariants

- **HTTP Method**: `POST`
- **Status Code**: Returns `201 Created` on success.
- **Auth Requirement**: Requires `admin.memberships.manage` permission via `require_permission`.
- **Uniqueness Constraint**: A product is uniquely identified by the combination of `slug` and `year`.
- **Date Auto-population**: If `start_date` or `end_date` are not provided in the payload, they default to January 1st and December 31st of the specified `year`, respectively.
- **Return Shape**: Returns a `TemporalProductRead` object, which includes the generated `id`.

## Gotchas

- **Slug/Year Collision**: Attempting to create a product with a `slug` and `year` combination that already exists results in a `400 Bad Request`. This is a strict uniqueness check on the database level.
- **Implicit Date Generation**: If an agent modifies the logic to allow null dates, they must account for the fact that the current implementation automatically fills `start_date` and `end_date` based on the `year` field.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.manage` permission.
- **Rate limit**: While this specific endpoint is not explicitly rate-limited in the code, commit `ec53704` indicates a general hardening of security/rate-limiting on auth and write endpoints.
- **Side effects**: Creating a product via this endpoint populates the `TemporalProduct` table, which is a dependency for merchandise visibility in seasonal contexts.

## External consumers

- `concorda-web::src/lib/api.ts::adminTemporalProductsApi.create`

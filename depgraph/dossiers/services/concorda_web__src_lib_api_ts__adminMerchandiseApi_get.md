---
node_id: concorda-web::src/lib/api.ts::adminMerchandiseApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1b18bddffa8a3c7f322676ea7c4a5edf30acd0ca1bce2429b22a14b25002a6a9
status: current
---

# adminMerchandiseApi.get

## Purpose

Provides an administrative interface for managing merchandise lifecycle. It allows for fetching, creating, updating, and deleting merchandise records. This is a distinct administrative-only surface used for backend management, separate from the public-facing or user-facing merchandise views.

## Invariants

- **Uses `fetchApiAuthenticated`** — all calls require a valid bearer token via the authenticated helper.
- **`get(id)` returns a single `Merchandise` object.**
- **`list(params)` supports an `include_inactive` flag.** This is passed as a query parameter to filter the returned set.
- **`create` and `update` expect a JSON body.** The `create` method specifically requires a `MerchandiseCreate` object to satisfy the API contract.
- **`delete` returns `void`.**

## Gotchas

- **Admin-only access required.** Because this uses `fetchApiAuthenticated`, the caller must have the appropriate administrative permissions/claims, or the request will fail at the API level.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level credentials).
- **Side effects**: Changes to merchandise via `create`, `update`, or `delete` will affect any UI components or checkout flows that display or sell these items.

## External consumers

None known.

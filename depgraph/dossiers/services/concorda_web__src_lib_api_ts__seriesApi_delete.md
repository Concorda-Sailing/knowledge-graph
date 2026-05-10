---
node_id: concorda-web::src/lib/api.ts::seriesApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9bd57e94a974c9b3234c3a19980a675d0e5416fcb86e208f571956736d3b1337
status: current
---

# seriesApi.delete

## Purpose

The `seriesApi.delete` method performs a destructive removal of a specific series via a `DELETE` request to `/api/series/{id}`. It is used when a user or administrator needs to permanently remove a series and its associated metadata from the system.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the `DELETE` verb to comply with the API contract.
- **Returns `void`** — The function returns a promise that resolves to nothing upon successful deletion.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the caller has a valid session/token.
- **Targeted by ID** — Requires a single `string` argument representing the unique identifier of the series.

## Gotchas

- **Destructive action** — Deleting a series is a permanent operation. Ensure the UI provides a confirmation step before calling this, as there is no "undo" or "soft delete" mechanism visible in this service layer.
- **Dependency on `SeriesDetail`** — While this method returns `void`, the existence of the series is tracked by the `SeriesDetail` type used in sibling methods like `list` and `get`.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Deleting a series will likely impact any components or pages that list or display series details, such as the `SeriesPage` and `SeriesDetailContent` in the admin dashboard.

## External consumers

None known.

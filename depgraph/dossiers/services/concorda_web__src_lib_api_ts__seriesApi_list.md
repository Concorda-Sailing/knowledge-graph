---
node_id: concorda-web::src/lib/api.ts::seriesApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 53c01afcd2520b5720ae02a3bdbb2866d6b74f512d9f7fc7e1592ddc6d039d25
status: llm_drafted
---

# seriesApi.list

## Purpose

Fetches the full list of all racing series currently managed by the system. It is the primary method for populating high-level administrative views and management dashboards. Use this when you need to list all series, whereas `seriesApi.get(id)` should be used for single-series detail views or when drilling into a specific series' configuration.

## Invariants

- **Returns a `SeriesDetail[]` array.** The response contains full metadata for each series, including `organizing_authorities` and `race_schedule`.
- **Requires authentication.** Uses `fetchApiAuthenticated`, meaning a valid bearer token must be present in the request headers.
- **GET method.** This specific method performs a standard `GET` request to `/api/series`.

## Gotchas

- **Data shape dependency.** Recent changes in `SailingEvent` (e.g., `config_slot_count` and `crew_pool_name`) suggest that the underlying data models for series-related entities are frequently evolving to support more granular UI badges.
- **Potential for stale UI.** Because this is a list-level fetch, it is often used in "Series Page" views (e.g., `SeriesPage` in `members/admin/events/series/page.tsx`). If a series is updated via `seriesApi.update`, the list view will not reflect changes until a fresh fetch is triggered.

## Cross-cutting concerns

- **Auth**: Depends on `fetchApiAuthenticated` for all calls.
- **Side effects**: Updates to series data via `seriesApi.update` or `seriesApi.delete` will affect the data displayed in the `SeriesPage` and the `AwardsContent` component.

## External consumers

- `concorda-web::src/app/members/admin/events/series/page.tsx` (SeriesPage)
- `concorda-web::src/app/members/awards/awards-content.tsx` (AwardsContent)

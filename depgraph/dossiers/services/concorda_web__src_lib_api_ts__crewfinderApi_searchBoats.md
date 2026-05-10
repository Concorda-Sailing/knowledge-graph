---
node_id: concorda-web::src/lib/api.ts::crewfinderApi.searchBoats
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 057d5878b183792e9d4f6854a5d6efee4c7b50b654b9fbfcae3192f62777f952
status: llm_drafted
---

# crewfinderApi.searchBoats

## Purpose

Provides a text-based search for boats within the Crewfinder module. It is distinct from the parameterized `searchBoats` (which filters by experience, position, and race area) by accepting a raw query string `q` for broader keyword matching. Use this when the user is performing a free-text search rather than applying structured filters.

## Invariants

- **Input is a raw string.** The query `q` is passed via `encodeURIComponent` to ensure special characters do not break the URL structure.
- **Returns `BoatSearchResult[]`.** The response is a typed array of boat search results.
- **Uses `fetchApiAuthenticated`.** This method requires a valid bearer token and will fail if the user is not authenticated.

## Gotchas

- **Search is not a filter.** Unlike the parameterized search method, this does not take `experience_level` or `race_area` as structured arguments; it relies on the backend's implementation of the `q` parameter.
- **Dependency on `fetchApiAuthenticated`.** If the authentication layer is modified, this method's ability to retrieve results is immediately impacted.

## Cross-cutting concerns

- **Auth**: Requires authentication via `fetchApiAuthenticated`.
- **Side effects**: Results from this search are consumed by the `BoatExclusionList` component to allow users to filter out specific boats from their view.

## External consumers

None known.

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
`crewfinderApi.searchBoats` provides a specialized search mechanism for finding boats within the Crewfinder service. It is distinct from the standard `searchBoats` (which likely handles broader criteria) by accepting a single string query `q` and returning an array of `BoatSearchResult` objects. Use this function when the UI requires a text-based autocomplete or a simple keyword search for boat names/details rather than a filtered parameter-based search.

## Invariants
* Performs a GET request to `/api/crewfinder/boats/search`.
* Requires authentication via `fetchApiAuthenticated`.
* The input parameter `q` is URI encoded using `encodeURIComponent` to prevent malformed query strings.
* Returns a Promise resolving to `BoatSearchResult[]`.

## Gotchas
* **Query Encoding**: The function uses `encodeURIComponent(q)` for the query string; ensure that any complex objects passed as `q` are pre-serialized or that the caller expects a string-only input.
* **Type Mismatch**: Ensure the consumer expects an array of `BoatSearchResult`; if the API returns a single object or a different shape, the type assertion will fail at runtime.

## Cross-cutting concerns
* **Auth**: Relies on `fetchApiAuthenticated` for session-based authorization.
* **Side Effects**: None identified for this specific search endpoint.

## External consumers
concorda-web::src/components/profile/boat-exclusion-list.tsx (via BoatExclusionList)

## Open questions
* It is unclear if the backend supports advanced search operators within the `q` string or if it is strictly a literal substring match.

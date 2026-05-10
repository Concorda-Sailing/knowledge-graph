---
node_id: GET::/api/crewfinder/boats/search
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c34db3bf9a14459d697d701240ef14f44a82dd1258299650145aa8b250462a6
status: current
---

# GET /api/crewfinder/boats/search

## Purpose

Provides a search mechanism for boats by name or sail number, primarily used for populating exclusion lists. It returns a list of `BoatSearchResult` objects containing the boat's identity and the name of its active owner. This is distinct from the general crewfinder profile list, as it focuses on the physical vessel rather than the person.

## Invariants

- **HTTP Method**: `GET`.
- **Authentication**: Requires a valid session via `require_auth`.
- **Return Shape**: A list of `BoatSearchResult` objects, each containing `id`, `sail_number`, `name`, and `owner_name`.
- **Search Pattern**: Uses an `ilike` pattern (`%q%`) to allow partial matches on both `name` and `sail_number`.
- **Result Limit**: The query is hard-capped at 50 results to prevent large-scale data exposure.

## Gotchas

- **PII Protection**: Per commit `33a37a3`, this endpoint must not expose sensitive person data. It only returns the `owner_name` (constructed from `first_name` and `last_name`) and does not return contact details or full `Person` objects.
- **Owner Lookup Logic**: The `owner_name` is derived by looking up the first `active` status `owner` in the `BoatCrew` table for that boat. If a boat has no active owner or the owner is not found, `owner_name` returns `None`.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth`.
- **Side effects**: Used by the boat-finder exclusion list logic in the web UI.

## External consumers

- `concorda-web::src/lib/api.ts::crewfinderApi.searchBoats`

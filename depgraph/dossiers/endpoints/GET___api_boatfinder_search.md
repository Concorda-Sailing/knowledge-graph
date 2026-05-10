---
node_id: GET::/api/boatfinder/search
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 53e4f4d119f036fe3507f604caf3cdc0c6624fb00a0f978bbf86d5869b67e8b2
status: llm_drafted
---

# GET /api/boatfinder/search

## Purpose

Provides a filtered list of boat profiles for the "Boat Finder" discovery feature. It allows users to search for boats based on `position`, `race_area`, and `ethos` while automatically enforcing privacy by excluding boats that the current user has explicitly blocked. This is distinct from the `/detail/{boat_id}` endpoint, which provides the full profile for a specific, known boat.

## Invariants

- **HTTP Method**: `GET`
- **Auth Requirement**: Requires `boatfinder.view` permission via `require_permission`.
- **Return Shape**: Returns a `list[BoatFinderProfile]`.
- **Exclusion Logic**: The `excluded_boat_ids` set is derived from the `SailingResume` of the `current_user`.
- **Filtering Logic**: If a query parameter (position, race_area, or ethos) is provided, the boat must match that criteria to be included in the result set.

## Gotchas

- **Exclusion List Dependency**: The exclusion logic relies on `user_resume.excluded_boat_ids`. If a user's `SailingResume` is missing or the field is null, the exclusion set defaults to an empty set, meaning no boats are hidden.
- **Race Area Nullability**: If `race_area` is provided in the query but the `BoatResume` has no `race_areas` defined, the boat is skipped (see `elif race_area and not br.race_areas` in source).

## Cross-cutting concerns

- **Auth**: Uses `require_permission("boatfinder.view")`.
- **Side effects**: Results populate the "Boat Finder" discovery UI.

## External consumers

None known.

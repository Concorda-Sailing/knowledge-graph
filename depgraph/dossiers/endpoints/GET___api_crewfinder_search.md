---
node_id: GET::/api/crewfinder/search
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5da4484fa793b09810e947081fd8dc80a74c4387d63425ac52ca360f0476922a
status: current
---

# GET /api/crewfinder/search

## Purpose

Provides a searchable directory of crew profiles and boat profiles. It allows users to filter by experience level, preferred position, and race area. This endpoint is distinct from the standard directory as it specifically handles the visibility logic for "opt-in" crew members and their associated boat profiles.

## Invariants

- **Requires `crewfinder.view` permission** via the `require_permission` dependency.
- **Returns `CrewfinderSearchResult`** containing two lists: `crew_profiles` and `boat_profiles`.
- **`can_see_crew` is hardcoded to `True`** for any authenticated user with the required permission.
- **`can_see_boats` depends on user preferences**; specifically, the user must have `crewfinder.opt_in` set to `True` in their preferences to see boat-related profiles.
- **Filters are optional**; `experience_level`, `position`, and `race_area` can all be `None`.

## Gotchas

- **PII Leakage Protection**: Per commit `33a37a3`, this endpoint was specifically hardened to close privilege gaps. The visibility of `email` and `phone_number` in the `CrewfinderProfile` is strictly controlled by the `show_email` and `show_phone` flags within the individual's `preferences` JSON.
- **Permission-based Filtering**: The query uses a `json_extract` on `Person.disabled_permissions` to ensure users who have been restricted from the crew finder are not returned in results, even if they meet the other filter criteria.
- **Boat Profile Visibility**: Unlike the crew list, boat profiles are only returned if the user has explicitly opted-in to the crew finder feature (see `has_published_crew` logic).

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `crewfinder.view` permission.
- **Side effects**: Changes to a user's `preferences` (specifically the `crewfinder.opt_in` flag) will immediately change the visibility of their boat profiles in this search result.

## External consumers

None known.

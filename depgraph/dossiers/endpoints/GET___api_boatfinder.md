---
node_id: GET::/api/boatfinder
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6190cd31a8ff573acc607a9d48ff68c9d62e84d9479f6c6f28d49c67d68fb911
status: current
---

# GET /api/boatfinder

## Purpose

Provides a public list of boat profiles that are currently "published" and looking for crew. It allows users to filter by position, race area, or ethos to find compatible vessels. This is distinct from the `/search` endpoint, which is an authenticated version that applies user-specific exclusion lists to hide boats the user has explicitly blocked.

## Invariants

- **Returns a list of `BoatFinderProfile` objects.** The response is a JSON array of objects containing boat and owner details.
- **Requires `published == True` for `BoatResume`.** Only resumes explicitly marked as published are included in the results.
- **Filters are additive.** If multiple query parameters (`position`, `race_area`, `ethos`) are provided, a profile must satisfy all non-null criteria to be returned.
- **`race_area` logic is strict.** If a `race_area` is provided in the query but the boat has no associated race areas, the boat is excluded from the results.

## Gotchas

- **`_get_boat_owner` can fail.** The loop uses a `try/except` block around `_get_boat_owner` (line 106) to catch `HTTPException`. If the owner lookup fails, the entire profile is skipped rather than returning a partial profile.
- **Exclusion lists are only for authenticated search.** The logic for `excluded_boat_ids` (lines 129-130) is specific to the `/search` sub-route and does not affect the base `/` endpoint.
- **Recent structural changes.** Per commit `ef1c3bd`, many helpers used in this router (like `_build_boat_profile`) were relocated to `utils/` or `scripts/`. Ensure any refactoring of the profile builder respects the new directory structure.

## Cross-cutting concerns

- **Auth**: The base endpoint is public. The `/search` sub-route requires `boatfinder.view` permission via `require_permission`.
- **Side effects**: Changes to `BoatResume.published` or `Boat.id` will immediately affect the visibility of profiles in this list.

## External consumers

None known.

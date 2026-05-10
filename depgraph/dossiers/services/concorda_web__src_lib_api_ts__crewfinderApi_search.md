---
node_id: concorda-web::src/lib/api.ts::crewfinderApi.search
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5db291f067e8a434b7ab6761674690058e815fe0b7a621f6ace13831643626be
status: current
---

# crewfinderApi.search

## Purpose

The `search` method provides a filtered view of available crew members based on specific skill and location criteria. It is distinct from the base `crewfinderApi` (which returns the full list of profiles) by allowing users to narrow results by `experience_level`, `position`, or `race_area`. This is the primary endpoint used when a user is looking for specific crew availability rather than browsing the full directory.

## Invariants

- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to access the `/api/crewfinder/search` endpoint.
- **Returns `CrewfinderSearchResult`** — the return type is a structured object containing the filtered list, not a raw array of profiles.
- **Query parameters are optional** — if `params` is undefined or empty, the function returns the unfiltered results from the base endpoint.
- **URL encoding is handled by `URLSearchParams`** — ensures that string values for position or race area are safely appended to the query string.

## Gotchas

- **Parameter mismatch** — unlike the base `crewfinderApi` call, this method specifically expects a structured object for `experience_level`, `position`, and `race_area`.
- **Recent logic shifts** — per commit `2d6b8a7`, the UI now relies on these types of filtered views to drive the "accepting-crew" status and config-aware counts on schedule cards; ensure any changes to the return shape don't break the regatta detail view.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Directly impacts the `CrewFinderPanel` component visibility and data density.

## External consumers

- `concorda-web::src/components/finder/crew-finder-panel.tsx::CrewFinderPanel`

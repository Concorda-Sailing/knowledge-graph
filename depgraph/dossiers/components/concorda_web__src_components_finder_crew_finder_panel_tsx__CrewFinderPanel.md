---
node_id: concorda-web::src/components/finder/crew-finder-panel.tsx::CrewFinderPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 70f12bcb19706fd29f83853c0e29684eda46e08dcfd6192a4e6d8b713abb482e
status: llm_drafted
---

# CrewFinderPanel

## Purpose

The primary UI panel for searching and discovering crew and boat profiles based on specific filters. It manages the local state for search criteria (experience level, position, race area) and orchestrates the data fetching from `crewfinderApi` and `constantsApi`. It is distinct from `BoatFinderPanel` in that it specifically handles the logic for excluding the user's own crew members from search results to prevent self-matching.

## Invariants

- **Filters are optional.** If a filter value is `"all"` or an empty string, it is sent as `undefined` to the API to ensure the backend treats it as a wildcard.
- **Fallback state on error.** If the API call fails (often due to authentication issues), the component sets `searchResult` to a specific shape with `can_see_crew: false` and `can_see_boats: false` to prevent UI crashes.
- **`myCrewIds` exclusion.** The component calculates a `Set` of person UUIDs belonging to the user's owned boats to ensure the user doesn't see their own crew in the search results.
- **`loadData` is memoized.** The function is wrapped in `useCallback` to prevent unnecessary effect triggers during re-renders.

## Gotchas

- **Layout stability.** Per commit `f36708e`, the card footers must be pinned to the bottom to prevent layout jitter when switching between grid and list views or when the "Contact" button is conditionally rendered.
- **Data fetching dependency.** The `useEffect` that populates `myCrewIds` depends on the `boats` array from `useBoats()`. If `boats` is empty, the effect returns early, which could lead to incorrect exclusion logic if the boat list loads asynchronously.
- **Search failure handling.** The `catch` block in `loadData` is a critical safety net; if the user's session expires, the component defaults to an empty result state rather than throwing an unhandled exception.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to retrieve the current user's ID and `useBoats` to fetch owned boat data for exclusion logic.
- **Websocket**: Listens to `sailing_resume.updated`, `sailing_resume.deleted`, and `boat_resume.updated` via `useWsFreshness` to ensure the panel remains fresh.
- **Side effects**: Rebuilds the search results when `experienceLevel`, `position`, or `raceArea` changes.

## External consumers

None known.

---
node_id: concorda-web::src/app/members/awards/awards-content.tsx::AwardsContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d507cc402d01b1ba7c605736aff82d2a160c67c31dca4d2653a1d938b9d46993
status: llm_drafted
---

# AwardsContent

## Purpose

Displays the biographical/historical content for a member's awards page, including a markdown-rendered introduction, a list of championship sections, and honoraria. It acts as the data-orchestrator for the awards view by fetching and aggregating `RegattaDetail` and `SeriesDetail` data via `regattaApi` and `seriesApi`. Use this component when you need to render the full historical context of a member's achievements rather than just a single event.

## Invariants

- **Fetches data on mount.** Uses `Promise.all` to concurrently fetch regattas and series to minimize loading states.
- **Graceful failure for API calls.** Both `regattaApi.list()` and `seriesApi.list()` are caught and return empty arrays to prevent the entire component from crashing if one endpoint fails.
- **`regattas === null` is the loading state.** The component displays `Skeleton` components while the promise is pending; once the promise resolves (even to an empty array), it switches to the content view.
- **`seriesById` is a memoized Map.** This allows `ChampionshipSection` to perform $O(1)$ lookups for series details without re-calculating the map on every render.

## Gotchas

- **Empty state vs. Loading state.** Because the catch blocks return `[]`, a failed API call results in a successful render of an empty list rather than a loading skeleton. If the API returns a 404 or 500, the user will see the `ChampionshipSection` loop run zero times without any error indication.

## Cross-cutting concerns

- **Auth**: Requires authenticated access to `regattaApi` and `seriesApi` to fetch list data.
- **Side effects**: The `regattas` and `series` data fetched here are passed down to `ChampionshipSection` to resolve specific event details.

## External consumers

- None known.

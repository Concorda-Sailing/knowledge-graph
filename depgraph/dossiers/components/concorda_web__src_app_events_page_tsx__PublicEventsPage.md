---
node_id: concorda-web::src/app/events/page.tsx::PublicEventsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f50b05ec15602b478b8ed066e922d933d22c0778d62704ac50dbae2720c3c272
status: current
---

# PublicEventsPage

## Purpose

The public-facing landing page for events, providing a list of upcoming events filtered by region. It serves as the entry point for unauthenticated users to discover events before logging in. It differs from `PublicEventPage` (the slug-specific view) by providing a high-level directory and organization-wide context.

## Invariants

- **Fetches organizations on mount** via `organizationsApi.list()` to populate the brand/context.
- **Uses `localStorage` for persistence** of the `region` filter via the `REGION_STORAGE_KEY` constant.
- **Filters events by region** through the `eventsApi.list({ region })` call.
- **Returns an empty array on fetch failure** to prevent the UI from crashing if the API is unreachable.

## Gotchas

- **Initialization sequence dependency**: The `region` state is not set until the `useEffect` for `localStorage` runs, and `events` are not fetched until `initialized` is true. This prevents the component from firing an API call with an empty/default region before the user's preference is loaded.
- **`region === "all"` logic**: The `regionParam` is explicitly set to `undefined` if the state is `"all"`. This is required to match the expected signature of `eventsApi.list` to ensure the API returns the full list rather than a filtered subset.

## Cross-cutting concerns

- **Auth**: None. This is a public-facing page; however, it provides the `Link` to `/login`.
- **Side effects**: Updates `localStorage` via `handleRegionChange` whenever a user selects a new region, affecting the filter state on subsequent visits.

## External consumers

None known.

## Open questions

- Should the region filter be moved to a URL search parameter (e.g., `?region=north`) instead of `localStorage` to allow users to share filtered views of the event list?

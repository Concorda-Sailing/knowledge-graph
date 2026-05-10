---
node_id: concorda-web::src/app/members/events/page.tsx::PublicEventsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f50b05ec15602b478b8ed066e922d933d22c0778d62704ac50dbae2720c3c272
status: current
---

# PublicEventsPage

## Purpose

The `PublicEventsPage` serves as the primary landing view for unauthenticated users to browse upcoming events and associated organizations. It manages the state for region-based filtering and persists the user's last selected region to `localStorage`. It acts as a high-level container that orchestrates data fetching from `eventsApi` and `organizationsApi` before passing the results down to the `EventsCalendar` presentation component.

## Invariants

- **Region persistence is client-side.** The `region` state is synchronized with `localStorage` via the `REGION_STORAGE_KEY` ("events_region_density") to ensure a consistent filtering experience across sessions.
- **Data fetching is sequential but decoupled.** Organizations are fetched once on mount, while events are fetched whenever the `region` or `initialized` state changes.
- **Error handling is silent.** If `eventsApi.list` or `organizationsApi.list` fails, the component catches the error and sets empty arrays to prevent a component crash.
- **`region === "all"` results in no filter.** When the region is set to "all", the `regionParam` passed to the API is `undefined`.

## Gotchas

- **`initialized` state is required for event fetching.** The `useEffect` for fetching events depends on `initialized` to prevent a race condition where the API is called with a default "all" value before the `localStorage` value is actually retrieved.
- **`localStorage` dependency.** Because the component reads from `localStorage` on mount, any SSR (Server Side Rendering) environments or automated tests that do not mock `localStorage` will encounter a mismatch or hydration error if the `region` state is not handled carefully.

## Cross-cutting concerns

- **Auth**: None (this is a public-facing page).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The `handleRegionChange` function updates `localStorage`, which may affect other components relying on the `events_region_filter` key.

## External consumers

None known.

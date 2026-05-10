---
node_id: concorda-web::src/app/members/directory/page.tsx::DirectoryPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bbe4adbb5b2f578c570b8a66c0f3bd3ea4acf4b1e9e8f366e3e37cc31002ee1a
status: llm_drafted
---

# DirectoryPage

## Purpose

The central view for the member directory, providing a searchable, paginated list of people and their associated organizations. It aggregates data from both `directoryApi` and `organizationsApi` to resolve organization names for member profiles. Use this component as the primary entry point for browsing the community, rather than building a new standalone list view.

## Invariants

- **Data fetching is dual-source.** It must fetch both `members` and `organizations` via `Promise.all` to ensure `getOrgNames` can resolve IDs to human-readable names.
- **Pagination is client-side.** The `filtered` list is sliced into `paged` segments based on the `PAGE_SIZE` of 24; changing the filter or search criteria resets the view to `page 1`.
- **Search is case-insensitive.** The filter logic converts both the search query and the target fields (`first_name`, `last_name`, `email`) to lowercase.
- **Alphabetical filtering is strict.** The `letter` filter uses `m.last_name.charAt(0).toUpperCase()` to match against the provided character.

## Gotchas

- **Mobile-specific UI constraints.** Per commit `6b2469c`, the alphabet filter is hidden on mobile devices to favor a search-only experience.
- **Layout rigidity.** Per commit `e16d26e`, the component is forced into a `card grid` view on mobile devices, regardless of the `view` state, to maintain consistency.
- **Empty state handling.** If `directoryApi.list()` or `organizationsApi.list()` fails, the `catch` block leaves the state empty without throwing, resulting in a blank directory rather than an error UI.

## Cross-cutting concerns

- **Auth**: None (relies on `directoryApi` and `organizationsApi` which handle their own authentication/session state).
- **Websocket**: Listens to `person.updated` and `directory.changed` via `useWsFreshness` to trigger a full re-fetch of the directory data.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Re-fetches the entire list when the WebSocket signals a change to the directory or person data.

## External consumers

None known.

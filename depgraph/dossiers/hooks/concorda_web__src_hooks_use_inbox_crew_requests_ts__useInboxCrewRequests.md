---
node_id: concorda-web::src/hooks/use-inbox-crew-requests.ts::useInboxCrewRequests
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f7d153ca1bd2e0faf4206850cb7cf8b2303cecca350bb7f0ef345f81cf893119
status: current
---

# useInboxCrewRequests

## Purpose

Provides a real-time subscription to pending crew requests for the user's inbox. It uses `useSyncExternalStore` to bridge the external `cache` state into the React lifecycle, ensuring that components like the `InboxNavItem` and `InboxList` stay in sync with the underlying data store. Use this instead of manual `useEffect` fetching when you need to display the current count or list of requests in the sidebar or main inbox view.

## Invariants

- **Returns a `refresh` function.** This is a direct reference to `fetchNow`, allowing components to manually trigger a re-fetch.
- **Uses a stale-while-revalidate pattern.** The `useEffect` triggers a fetch if the `cache.lastFetched` delta exceeds `STALE_MS`.
- **Provides a fallback snapshot.** `getServerSnapshot` returns an empty state (`items: []`, `isLoading: false`) to prevent hydration mismatches during SSR/initial load.

## Gotchas

- **Automatic re-fetch on mount.** Because of the `useEffect` logic, any component mounting this hook will trigger a `fetchNow()` if the cache is older than `STALE_MS`. This can lead to unexpected network activity if multiple components (like `InboxNavItem` and `InboxList`) mount simultaneously.

## Cross-cutting concerns

- **Auth**: Relies on the authenticated user context to fetch specific crew requests.
- **Side effects**: Triggers updates to the `InboxNavItem` (sidebar count) and the `InboxList` (main view).

## External consumers

None known.

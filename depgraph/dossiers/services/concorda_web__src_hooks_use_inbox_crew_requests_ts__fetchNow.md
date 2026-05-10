---
node_id: concorda-web::src/hooks/use-inbox-crew-requests.ts::fetchNow
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ce01c1b46bdba4492b0a0ede1b15abdee23f9ab1fa79133d5179a89d3e3d542f
status: current
---

# fetchNow

## Purpose

Provides a synchronized, cached state of incoming crew requests for the inbox. It uses a `useSyncExternalStore` pattern to manage a local cache of data fetched via `eventsApi.listInboxCrewRequests()`. This ensures that multiple components consuming the hook see a consistent view of the inbox without triggering redundant, simultaneous network requests.

## Invariants

- **Singletons for Inflight Requests**: The `inflight` promise ensures that only one network request is active at a time; subsequent calls to `fetchNow` while a request is pending will return the existing promise and increment a `pending` flag.
- **Cache Structure**: The cache always contains an `items` array, an `isLoading` boolean, and a `lastFetched` timestamp.
- **Server-Side Fallback**: `getServerSnapshot` returns an empty, non-loading state to ensure compatibility with SSR/hydration without breaking the `useSyncExternalStore` contract.

## Gotchas

- **Race condition handling**: The `pending` flag and recursive `fetchNow()` call in the `.finally` block are used to ensure that if multiple requests are queued during a single flight, the most recent one is eventually honored.
- **Stale data threshold**: The hook automatically triggers a fetch on mount if `Date.now() - cache.lastFetched > STALE_MS`.

## Cross-cutting concerns

- **Auth**: Implicitly depends on the authentication state required by `eventsApi.listInboxCrewRequests()`.
- **Side effects**: Triggers updates to the inbox UI components that consume `useInboxCrewRequests`.

## External consumers

None known.

## Open questions

- Commit `be6b4d5` added "pending crew requests + planning doc" to the inbox; it is unclear if the `items` array should be further subdivided into "pending" vs "active" categories at the hook level or if the consumer should handle the filtering.

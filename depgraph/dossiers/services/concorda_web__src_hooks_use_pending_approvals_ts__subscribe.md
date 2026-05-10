---
node_id: concorda-web::src/hooks/use-pending-approvals.ts::subscribe
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2efd79657245f82e3774a04d82faffd131d05e46223408d71165b450fc7e4e59
status: current
---

# subscribe

## Purpose

The `subscribe` function manages the listener registry for the `usePendingApprovals` external store. It is a low-level utility used by `useSyncExternalStore` to notify React when the underlying `cache` has been updated via `fetchNow`. It is distinct from the hook itself, acting as the bridge between the imperative cache updates and the declarative React lifecycle.

## Invariants

- **Listener Registry Management**: `listeners.add(fn)` registers a callback, and the returned cleanup function must call `listeners.delete(fn)` to prevent memory leaks.
- **Synchronous Execution**: The function is designed for `useSyncExternalStore`, meaning the snapshot returned by `getSnapshot` must be stable to avoid infinite re-render loops.
- **Single Source of Truth**: All updates to the `incoming`, `outgoing`, or `urgent` arrays must be routed through the internal `cache` and trigger this subscription mechanism.

## Gotchas

- **Manual Refresh Requirement**: Because this is a custom external store, the UI will not automatically reflect new data unless `fetchNow()` is triggered. Per commit `8b87dd3`, the hook was introduced to handle the specific "inbox" state, but developers must ensure `refresh()` is called if they expect real-time updates without a page reload.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Triggers re-renders for any component consuming `usePendingApprovals`, specifically affecting the visibility of the "urgent" approval list.

## External consumers

None known.

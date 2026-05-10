---
node_id: concorda-web::src/contexts/websocket-context.tsx::useWebSocket
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d998c64fd0477d09ee88287bb88890a2614f8658bae0b6b415b2b6ae31a9ac58
status: llm_drafted
---

# useWebSocket

## Purpose

Provides access to the `WebSocketContext` state, specifically the `isDirty` flag and the `clearDirty` function. It is used by downstream hooks to track when the local client state has diverged from the server-side truth due to pending updates or unacknowledged messages. An agent should use this when a component needs to react to "dirty" states (e.g., showing a loading spinner or a "syncing" indicator) rather than implementing its own local state tracking.

## Invariants

- **Context Requirement**: Must be called within a `WebSocketProvider` hierarchy; otherwise, it throws a runtime error.
- **Return Shape**: Returns an object containing `{ isDirty: boolean, clearDirty: () => void }`.
- **State Management**: `isDirty` is a boolean flag that tracks the synchronization status of the websocket connection.

## Gotchas

- **Strict Provider Dependency**: If a component calls `useWebSocket` outside of the provider, it triggers a hard error: `"useWebSocket must be used within a WebSocketProvider"`. This is a common failure point when moving hooks into new feature branches or testing environments that lack the provider wrapper.
- **Recent UI Improvements**: Per commit `54d6153`, the addition of the "boatfinder page" and "crew invite system" relies on the stability of the websocket state. Changes to how `isDirty` is toggled could break the real-time feedback loops in these new features.

## Cross-cutting concerns

- **Auth**: None (relies on the existing auth context for the underlying connection, but this hook itself is agnostic).
- **Websocket**: Tracks the synchronization state of the active connection.
- **Side effects**: Used by `useBoats` and `useWsFreshness` to determine if local data is stale or currently being updated.

## External consumers

None known.

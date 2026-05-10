---
node_id: concorda-web::src/hooks/use-ws-freshness.ts::useWsFreshness
node_kind: hook
feature: realtime-updates
last_reviewed: 2026-05-09
last_reviewed_against_hash: df2001dda5a57e0f2d9ed9a6692c05a46a3a380ed0998f76d4dc9b1f7d8dfbd8
status: current
---

# useWsFreshness

## Purpose

The web side of the realtime-update story. A page that watches one or more websocket event types calls `useWsFreshness(["boat_crew.updated"], refetch)`; if any of those events fired *while the page was unmounted*, the hook calls `refetch()` on the next mount.

Pairs with the API's `broadcast_event` (see that dossier). Without this hook, websocket events would only update components that happen to be mounted when the event fires; navigating away and back would not pick up a missed event.

14 components use it.

## Invariants

- **Skips the initial mount.** A page is already fetching its data on first render; refetching again is wasteful. The `hasChecked.current = true` ref makes the first render a no-op.
- **Reads from `useWebSocket()` context.** That context aggregates events into a `dirty` set keyed by event type. `clearDirty(...)` is the only way to consume the dirty state.
- **`refetch` is called *unconditionally* when dirty.** No throttle, no debounce. If you pass a heavy refetch, this can fire multiple times in quick navigation. Memoize the refetch callback if it's expensive.
- **Event-type strings must match the API constants.** `"boat_crew.updated"`, `"event.updated"`, etc. Renaming an event in the API requires updating every `useWsFreshness([...])` call site.

## Gotchas

- **`useEffect` has no deps.** It runs on every render. Intentional — the hook is cheap and we want it responsive to navigation. But: if `eventTypes` is constructed inline (`useWsFreshness(["x"], cb)`), the array identity changes every render. That doesn't matter today (no deps array) but if you ever convert this to a deps-aware variant, you'll need to memoize callers' arrays.
- **`clearDirty` only clears the events you pass.** Other components watching different events still see them as dirty. That's correct — but if you `clearDirty(["a"])` and another component watches `["a", "b"]`, that other component will only see `"b"` as dirty even if event `"a"` was the trigger.
- **Single-worker constraint inherited from `broadcast_event`.** This hook only sees what the websocket fanout sees. With multi-worker uvicorn (which we aren't running today), some browsers connected to the "wrong" worker would miss events.

## Cross-cutting concerns

- **Direct dependent of `useWebSocket` context** which manages the actual WS connection.
- **Indirectly tied to `broadcast_event` server-side**: the event-type strings must agree.
- **Test impact:** Playwright specs that assert post-mutation state typically just refetch via `api.get(...)` rather than waiting for the websocket; this hook is purely a UX optimization.

## External consumers

- N/A — internal to the web app.

## Open questions

- Should the hook accept a debounce option for expensive refetches?
- Consider centralizing the event-type strings into a shared constants module so a rename in the API auto-flips the structural_hash on every consumer here.

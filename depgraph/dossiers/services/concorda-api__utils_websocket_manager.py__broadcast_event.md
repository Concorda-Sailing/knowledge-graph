---
node_id: concorda-api::utils/websocket_manager.py::broadcast_event
node_kind: service
feature: realtime-updates
last_reviewed: 2026-05-09
last_reviewed_against_hash: 8e4ed183802c905413b75f5f1a7ef2870f8d2d5b417a6188a7201b8f11526324
status: current
---

# broadcast_event

## Purpose

Push a typed event onto the websocket fanout for every connected client. Sync route handlers call this when they mutate state that other browsers are likely watching — boat crew rosters, event registrations, regatta schedules. Each client receives `{type: <event_type>, id: <entity_id>}` and refetches the implicated resource.

This is the only mechanism the API uses to invalidate other browsers' cached views in real time. Without it, a crew change made by one user takes effect for everyone else only on the next manual refresh or hook poll.

## Invariants

- **Sync-callable from any route handler.** The function is not `async`. Internally it schedules `manager.broadcast(...)` on the running event loop via `call_soon_threadsafe`. Route handlers that are themselves async should still call this — it just defers a coroutine onto the loop they're already on.
- **Fire-and-forget.** No return value, no awaitable. Callers do not get back-pressure or delivery confirmation. If the websocket is broken, the client will disconnect and reconnect; in the meantime the event is lost.
- **`entity_id` is the resource id, not a user id.** Consumers use it to know what to refetch. Always pass the boat id / event id / regatta id, not the actor's person id.
- **`event_type` is a stable string convention.** Defined as module constants (e.g. `BOAT_CREW_UPDATED = "boat_crew.updated"`). Frontend `useWsFreshness` matches on these strings — renaming an event silently breaks every consumer until they redeploy.
- **No-op on missing event loop.** If `_event_loop is None` (e.g., if `set_event_loop()` wasn't called at startup), broadcast is logged and skipped. Tests that don't init the loop will see this as a warning, not an error.

## Gotchas

- **41 endpoints emit events.** Adding a new event type for cross-page invalidation is cheap; renaming an existing one is expensive because every web/expo consumer's `useWsFreshness('boat_crew.updated')` is a string match.
- **The connection list is held in a process-local `ConnectionManager`.** This **does not work across multiple uvicorn workers** — see memory `feedback_rate_limiter_single_worker`. The system depends on `--workers 1` until we add Redis pub/sub or move to an ASGI broadcaster.
- **`active_connections.copy()` in `broadcast`** is intentional: send-failures remove the connection while iterating, so we iterate a snapshot.
- **Errors during send are silently swallowed.** A broken connection gets removed but the failure is invisible to the caller. This is correct (fire-and-forget) but means that if every consumer happens to be disconnected, the broadcast is a no-op and you'd never know.

## Cross-cutting concerns

- **Workers:** Single-worker constraint until Redis fanout lands.
- **Auth:** Connections currently authenticate via a token in the websocket query string at `/api/ws`. If that's broken, broadcasts go to nobody.
- **Test hosts:** Test environment websockets connect through Caddy at `wss://test.members.massbaysailing.org/api/ws`; mismatch with the API base URL is a common test-flake source.
- **Stop hook:** No tests directly verify broadcast — they verify the *side effects* (refetched data shows new state).

## External consumers

- **Web** via `useWsFreshness` hook (14 dependents) and indirectly through every component that subscribes for refresh.
- **Expo iOS app**: when active, will need the same event-string contract honored. Don't rename event constants.

## Open questions

- Should we add an event-replay buffer so reconnecting clients can catch up on what they missed?
- Move to Redis pub/sub before scaling beyond 1 worker.

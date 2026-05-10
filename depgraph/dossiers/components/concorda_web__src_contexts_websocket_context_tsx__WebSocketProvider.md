---
node_id: concorda-web::src/contexts/websocket-context.tsx::WebSocketProvider
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4737a1a4e6e7c8d05368323e0a2265a8bc8f416d7d979ca32b57a1b24a061c86
status: llm_drafted
---

# WebSocketProvider

## Purpose

The `WebSocketProvider` manages the lifecycle of the real-time connection for the web application. It ensures a persistent connection is established once a user is authenticated via `useAuth`, and provides a mechanism to track which event types have been "seen" via the `dirtyRef` set. It is distinct from `useWebSocket` (the consumer hook) by being the provider that actually manages the `WebSocket` instance, reconnection logic, and the `isDirty` state tracking.

## Invariants

- **Connection is gated by `isAuthenticated`** — The socket only attempts to connect if the user is logged in; it will not attempt to connect if `isAuthenticated` is false.
- **Exponential backoff is mandatory** — Reconnection attempts use a base of 3000ms and double with each failure up to a 60,000ms cap to prevent server hammering.
- **`MAX_FAILS_BEFORE_GIVE_UP` is 8** — After 8 consecutive failed connection attempts (specifically those where the connection fails to open), the provider stops attempting to reconnect.
- **`dirtyRef` tracks event types** — The `onmessage` handler populates a `Set` of strings representing the types of messages received, allowing components to check if they need to refresh data.

## Gotchas

- **Auth-failure loop protection** — Per the source comment, the provider is designed to prevent an "endless reconnect storm" when a stale or revoked token causes the server to reject the handshake with a 403. The `failCountRef` tracks these failures to ensure the client eventually gives up rather than hammering the API.
- **Intentional close vs. Error close** — The `useEffect` cleanup explicitly sets `ws.onclose = null` before calling `close()` to prevent the reconnection logic from triggering during a standard logout or unmount.

## Cross-cutting concerns

- **Auth**: Directly depends on `useAuth` to trigger the connection lifecycle.
- **Websocket**: Listens for all incoming messages and populates `dirtyRef` with the `data.type` field.
- **Side effects**: Reconnection logic is critical for features that rely on real-time updates, such as the crew invite system and boatfinder page (see commit `54d6153`).

## External consumers

None known.

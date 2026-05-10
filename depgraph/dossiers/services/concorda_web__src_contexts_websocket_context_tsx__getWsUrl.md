---
node_id: concorda-web::src/contexts/websocket-context.tsx::getWsUrl
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8bb03005b9f158cef65cd988224f2e975f31fe6e28adef2d7127eab65a6ffd3f
status: llm_drafted
---

# getWsUrl

## Purpose

Constructs the full WebSocket URL including the authentication token as a query parameter. It handles the distinction between local development environments (where Next.js rewrites fail to proxy WS upgrades) and production environments. Use this to ensure the `WebSocket` instance connects to the correct endpoint with valid credentials.

## Invariants

- **Returns an empty string** if `window` is undefined (SSR safety) or if `auth_token` is missing from `localStorage`.
- **Hardcodes the port to 6400** when `hostname` is `localhost` or `127.0.0.1` to bypass Next.js rewrite limitations.
- **Appends the token via URI encoding** as a query parameter (`?token=...`) to satisfy the API's handshake requirements.
- **Uses the current window protocol** (`ws:` or `wss:`) based on whether the site is running on `http:` or `https:`.

## Gotchas

- **The server rejects the handshake with 403** if the token is invalid or expired, which triggers an immediate `onclose` event. This is why `failCountRef.current` is tracked in the provider to prevent a "reconnect storm" (see `MAX_FAILS_BEFORE_GIVE_UP`).
- **Local development requires port 6400.** If the API is running on a different port than the Next.js dev server, the `hostname === "localhost"` check is the only way to ensure the connection reaches the backend.

## Cross-cutting concerns

- **Auth**: Relies on the presence of `auth_token` in `localStorage`.
- **Websocket**: Used by `WebSocketProvider` to establish the connection; failure to connect results in an exponential backoff retry loop.
- **Side effects**: The `onmessage` handler in the provider populates `dirtyRef.current` with event types, which signals components to refresh data.

## External consumers

None known.

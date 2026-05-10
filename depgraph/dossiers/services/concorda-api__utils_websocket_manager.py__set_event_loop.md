---
node_id: concorda-api::utils/websocket_manager.py::set_event_loop
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9986d2aa5319178cf6443bdfcc4c8509a92b5a23746a16d6c34ec58f1212fd5c
status: llm_drafted
---

# set_event_loop

## Purpose

Sets the global `_event_loop` instance for the WebSocket manager. This is a required initialization step to allow synchronous route handlers to trigger asynchronous broadcasts via `broadcast_event`. Without calling this, any attempt to broadcast from a sync context will fail silently with a warning.

## Invariants

- **Must be called during application startup** to ensure `_event_loop` is not `None` when the first event is broadcast.
- **The provided loop must be an `asyncio.AbstractEventLoop`** compatible with the running server process.
- **`_event_loop` is a global singleton** within the module; calling this multiple times replaces the existing loop.

## Gotchas

- **Silent failure if not initialized.** If `set_event_loop` is not called before a sync route attempts to use `broadcast_event`, the system logs a warning and skips the broadcast rather than raising an exception (per the `if _event_loop is None` guard).
- **Relocation dependency.** Per commit `ef1c3bd`, this logic was moved from the root into `utils/`. Any legacy code attempting to initialize the loop via a different path may fail to populate this specific global variable.

## Cross-cutting concerns

- **Websocket**: Essential for the execution of all events defined in this module (e.g., `BOAT_UPDATED`, `DIRECTORY_CHANGED`).
- **Side effects**: Required for the `broadcast_event` helper to successfully push updates to active `ConnectionManager` connections.

## External consumers

None known.

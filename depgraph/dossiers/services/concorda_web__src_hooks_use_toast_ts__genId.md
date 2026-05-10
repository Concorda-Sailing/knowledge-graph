---
node_id: concorda-web::src/hooks/use-toast.ts::genId
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c1ae571a4b93aff0ace129ef0aae90dae53c990c563f3be851c18d9f7d930ac
status: current
---

# genId

## Purpose

Generates a unique, incremental string ID for toast notifications. It is a private utility used by the `use-toast` hook to ensure every toast instance has a distinct identifier for the reducer to track, update, or dismiss.

## Invariants

- **Returns a string.** The output is always a string representation of the incremented `count`.
- **Uses a modulo operation.** The `count` is reset via `% Number.MAX_SAFE_INTEGER` to prevent integer overflow during long-running sessions.
- **Increments monotonically.** Every call to `genId()` increases the internal `count` by 1 before returning the value.

## Gotchas

- **Stateful side effect.** Because `count` is a module-level variable, the ID sequence is tied to the lifecycle of the web app's runtime; it is not a UUID and is not globally unique across different browser sessions or users.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Directly drives the lifecycle of `ToasterToast` objects in the `use-toast` reducer, including the `TOAST_REMOVE_DELAY` logic.

## External consumers

None known.

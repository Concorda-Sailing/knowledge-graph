---
node_id: concorda-web::src/hooks/use-toast.ts::reducer
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d4b10dbaa1b029d2a959aaa38a1de358a671ddb18f860afbf1e86a9ecff9dae6
status: current
---

# reducer

## Purpose

The state reducer for the global toast notification system. It manages the lifecycle of toast notifications, including adding, updating, dismissing (setting `open: false`), and removing (hard deletion) from the state. It is the core logic used by the `dispatch` function to ensure the UI reflects the current queue of transient messages.

## Invariants

- **`TOAST_LIMIT` is enforced** — The `ADD_TO_TOAST` case uses `.slice(0, TOAST_LIMIT)` to prevent the toast array from growing indefinitely.
- **`DISMISS_TOAST` is a soft removal** — This action sets `open: false` on the target toast(s) rather than deleting them immediately, allowing for exit animations.
- **`REMOVE_TOAST` is a hard removal** — If `action.toastId` is undefined, the entire toast array is cleared.
- **State is immutable** — Every case returns a new state object via spread operators or `.map`/`.filter` to ensure React compatibility.

## Gotchas

- **`DISMISS_TOAST`-induced side effects** — Calling `DISMISS_TOAST` without a `toastId` triggers `addToRemoveQueue` for every toast in the current state, which may trigger a cascade of `REMOVE_TOAST` actions via the `TOAST_REMOVE_DELAY` logic in the `dispatch` function.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: The `dispatch` function (sibling) triggers `addToRemoveQueue` and manages `toastTimeouts.set`, which controls the actual removal of elements from the DOM.

## External consumers

None known.

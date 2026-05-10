---
node_id: concorda-web::src/hooks/use-toast.ts::toast
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c786e13cc0805d0152ab18b99b6ed8ebdf104b8137ec61b6513107951a7033a0
status: llm_drafted
---

# toast

## Purpose

Provides a global, singleton-based toast notification system for the web app. It allows components to trigger ephemeral UI alerts (success, error, info) that are managed via a central `dispatch` and `reducer` pattern. Use `toast()` for imperative triggers from non-React code or event handlers, and `useToast()` for standard component-level access.

## Invariants

- **`toast()` returns a control object.** Every call returns an object containing the unique `id`, a `dismiss` function, and an `update` function.
- **`onOpenChange` triggers dismissal.** If the `onOpenChange` prop is provided, it is responsible for calling `dismiss()` when the state transitions to closed.
- **State is managed via a listener pattern.** The `useToast` hook subscribes to a global `listeners` array to ensure all components consuming the hook react to the same toast state.
- **`id` is generated via `genId()`.** Every toast must have a unique identifier to allow for targeted `DISMISS_TOAST` actions.

## Gotchas

- **`useToast` dependency array.** The `useEffect` in `useToast` depends on `[state]`. If the state updates rapidly, the listener is removed and re-added, which is necessary to keep the `setState` reference current for the global `listeners` array.
- **Manual dismissal requirement.** If a component uses the `open` property from a toast, it must ensure the `onOpenChange` logic (or a manual call to `dismiss`) is respected, otherwise, the toast may persist in the state indefinitely.

## Cross-cutting concerns

- **Auth**: none.
- **Websocket**: none.
- **Audit**: N.
- **Rate limit**: none.
- **Side effects**: Used for displaying transient feedback from registration flows and payment status updates (per commit `01bc16e`).

## External consumers

None known.

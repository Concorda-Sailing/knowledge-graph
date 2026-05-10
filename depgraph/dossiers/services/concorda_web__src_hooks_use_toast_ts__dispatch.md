---
node_id: concorda-web::src/hooks/use-toast.ts::dispatch
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eac92bcd58a6fe7c864652421ba7ad3bef81faabb3e8e94c6e05aead522dd6c3
status: llm_drafted
---

# dispatch

## Purpose

The central state dispatcher for the application's toast notification system. It manages a global `memoryState` and a registry of `listeners` to ensure that toast notifications (additions, updates, and dismissals) are synchronized across all components using the `useToast` hook. While `useToast` provides the React-specific hook interface, `dispatch` is the underlying engine that drives the state transitions.

## Invariants

- **State is globally shared.** The `memoryState` lives outside the React lifecycle, ensuring that a toast triggered from a non-component context (via the exported `toast` function) is visible to all components using `useToast`.
- **`dispatch` is the only way to mutate state.** All changes to the `toasts` array must go through the `reducer` via a `dispatch` call to ensure the `listeners` are notified.
- **`onOpenChange` triggers dismissal.** If a toast is closed via its `onOpenChange` prop, the `dismiss` function is called, which dispatches a `DISMISS_TOAST` action.

## Gotchas

- **Manual listener management.** The `useToast` hook manually pushes `setState` into the `listeners` array and performs a manual cleanup in the `useEffect` return. If a developer adds a new way to interact with the state that bypasses this registry, the UI will become out of sync with the `memoryState`.
- **`toast` function is a side-effect generator.** Calling the exported `toast` function immediately invokes `dispatch` (via `ADD_TOAST`). This can be used outside of React component lifecycles, but it relies on the `genId()` function to ensure uniqueness.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Triggers UI updates for any component subscribing to `useToast`, such as global notification banners or snackbar components.

## External consumers

None known.

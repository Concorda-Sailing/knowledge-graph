---
node_id: concorda-web::src/components/back-button.tsx::BackButton
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2daecb2697ad5f8b208800604e4f69bb3035eb15ea561668a8071f1bccb86e45
status: current
---

# BackButton

## Purpose

A browser-history-aware navigation component. It intelligently decides whether to trigger a `router.back()` or navigate to a specific `fallback` URL based on the user's current session depth. Use this instead of a standard `Link` when you want to preserve the user's natural "back" flow, but provide a safe exit path (like a dashboard or home page) if they landed on the page via a direct link or a fresh tab.

## Invariants

- **History-dependent rendering.** The component returns `null` during the initial mount phase (while `hasHistory` is `null`) to prevent a flash of incorrect UI.
- **Fallback logic.** If `window.history.length <= 1`, it renders a `Link` to the `fallback` prop; otherwise, it executes `router.back()`.
- **Prop-driven styling.** The `variant` and `size` props must map to the existing `Button` component's design system to ensure visual consistency.

## Gotchas

- **Heuristic is a snapshot.** The `hasHistory` state is captured once on mount via `useEffect`. If the user navigates within the same page after the component has mounted, the `hasHistory` value will not update, which is intentional to prevent the button from changing behavior mid-session.
- **SSR/Hydration mismatch.** Because it relies on `window.history`, the component returns `null` on the server. This is a deliberate design choice to avoid hydration errors in Next.js/React environments.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.

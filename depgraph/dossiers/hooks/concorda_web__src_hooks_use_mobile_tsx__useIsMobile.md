---
node_id: concorda-web::src/hooks/use-mobile.tsx::useIsMobile
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8ae1bd66b21ef7b7a2ebba21233eb8c420f0f9e1bdde424ce668fcabde0be1c8
status: llm_drafted
---

# useIsMobile

## Purpose

Provides a boolean flag indicating if the current viewport width is below the `MOBILE_BREAKPOINT`. It is used to conditionally render or adjust layouts (e.g., switching from a horizontal tab bar to a vertical stack) when the user is on a mobile device. Use this instead of raw `window.innerWidth` checks to ensure the component reacts to window resizing.

## Invariants

- **Breakpoint is fixed at 768px.** Any change to the layout logic must respect this constant.
- **Initial state is `false`.** The hook defaults to `false` on mount before the first `useEffect` execution.
- **Client-side only.** The empty dependency array in `useEffect` ensures the `window` object is accessed only after the component mounts, preventing SSR/hydration mismatch errors in environments where `window` is undefined.

## Gotchas

- **Hydration Mismatch:** Because `isMobile` defaults to `false` and the `useEffect` runs after mount, there is a single-frame "flicker" where a mobile user might see the desktop layout before the `isMobile` state updates to `true`. Components relying on this for critical layout-shifting (like a navigation bar) must account for this initial `false` state.

## Cross-cutting concerns

- **Side effects**: Affects the layout density and visibility of components in `BoatProfileTab` and `ScheduleTab`.

## External consumers

None known.

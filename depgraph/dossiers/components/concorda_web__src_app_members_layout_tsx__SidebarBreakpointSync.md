---
node_id: concorda-web::src/app/members/layout.tsx::SidebarBreakpointSync
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fe9a467d366d8a3328528ddbff605b5daf50c30159da2708f5910dc4332d8c4
status: llm_drafted
---

# SidebarBreakpointSync

## Purpose

The `SidebarBreakpointSync` component manages the automatic collapse/expand state of the sidebar based on viewport width. It ensures that when a user transitions from a mobile view to a desktop view (or vice versa), the sidebar state remains consistent with the layout requirements. It is a non-rendering helper used to bridge the gap between the `SidebarProvider` state and the window's media query.

## Invariants

- **Uses a `useRef` for `setOpen`** — The `setOpen` function from `useSidebar` is stored in a ref to avoid re-triggering the `useEffect` whenever the `SidebarProvider` identity changes.
- **Monitors `(min-width: 1024px)`** — The component specifically listens for the transition across the 1024px threshold to trigger the `apply` logic.
- **Returns `null`** — This is a logic-only component; it does not render any DOM elements itself.
- **`isMobile` guard** — The effect only attaches the media query listener if `isMobile` is false, preventing conflicting logic during mobile-specific rendering phases.

## Gotchas

- **Identity stability is required** — As noted in the source comments, if the component depended on `setOpen` directly in the dependency array, the `SidebarProvider`'s internal re-renders would cause the effect to re-run and potentially undo user-initiated toggles on desktop.
- **Mobile-specific layout behavior** — Per commit `c3666645`, the layout was adjusted to ensure the `SidebarInset` handles vertical scrolling and minimum widths correctly when the sidebar is active on mobile.

## Cross-cutting concerns

- **Auth**: Indirectly depends on `useAuth` via the parent `DashboardLayout`; the sidebar is only mounted if `isAuthenticated` is true.
- **Side effects**: Controls the visibility/expansion state of the `SidebarNav` and `SidebarTrigger` components within the `DashboardLayout`.

## External consumers

None known.

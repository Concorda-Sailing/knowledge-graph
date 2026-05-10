---
node_id: concorda-web::src/components/ui/sidebar.tsx::useSidebar
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 84370d556a88ee22b67203aa7fa8bd08141722283906dcab4aa1d632dc730a55
status: current
---

# useSidebar

## Purpose

Read accessor for sidebar UI state. Returns the `SidebarContext` value: `state` (`"expanded" | "collapsed"`), `open`/`setOpen` (desktop), `openMobile`/`setOpenMobile` (mobile sheet), `isMobile` (viewport flag from `useIsMobile`), and `toggleSidebar` (does the right thing per viewport). The provider (`SidebarProvider`) owns the underlying `useState`, the cookie write on every `setOpen`, and the Cmd/Ctrl+B global keyboard shortcut — `useSidebar` is just the consumer-side handle.

## Invariants

- Must be called inside a `SidebarProvider` subtree; otherwise throws `"useSidebar must be used within a SidebarProvider."` at render time.
- `state === "expanded"` iff `open === true`. Consumers should treat `state` and `open` as the same signal in two shapes (string for `data-state` attributes, boolean for logic).
- On mobile (`isMobile === true`), `open` is stale/irrelevant for visibility — the sheet uses `openMobile`. `toggleSidebar` switches which one it flips based on `isMobile`, so consumers rarely need to branch themselves.
- The hook itself is pure context read; all side effects (cookie persistence, keyboard shortcut, mobile detection) live in the provider.

## Gotchas

- `"use client"` file. Calling `useSidebar` from a server component will fail.
- `setOpen` persists to a `sidebar_state` cookie on every call (7-day max-age). There is no "set without persist" escape hatch; toggles from any consumer write the cookie.
- `isMobile` comes from `useIsMobile`, which is viewport-based and can flip on resize — `toggleSidebar`'s branch is re-evaluated on each call, so a desktop-rendered trigger that crosses the breakpoint will start toggling the mobile sheet instead.
- The provider supports controlled mode via `open` / `onOpenChange` props; in that mode `_open` is ignored but the cookie write still happens.

## Cross-cutting concerns

- Pairs with `SidebarProvider` (state owner, cookie writer, keyboard shortcut binder) and `SidebarContext` (the typed shape).
- Depends on `useIsMobile` from `@/hooks/use-mobile` for the desktop/mobile split.
- The cookie (`sidebar_state`) is the only persistence boundary — anything else reading the user's last sidebar choice should read that cookie, not re-derive it.

## External consumers

Inside this file: `SidebarTrigger` (toggle button), `SidebarRail` (drag-edge toggle), `Sidebar` (reads `isMobile`/`state`/`openMobile`/`setOpenMobile` to pick between Sheet and desktop chrome), `SidebarMenuButton` (reads `isMobile`/`state` to suppress tooltip when expanded or on mobile). No other files in `concorda-web` import `useSidebar` directly — the layout consumes it transitively via the components above.

## Open questions

- Should controlled mode (`open` prop on `SidebarProvider`) skip the cookie write? Currently it persists even when the parent owns state, which can desync if the parent's source of truth disagrees with the cookie on next mount.
- Is the Cmd/Ctrl+B shortcut documented anywhere user-facing? It's bound unconditionally for every mounted provider and will fire even when focus is in an input.
- The `mobileTitle` prop on `Sidebar` defaults to `"Menu"` — should this hook surface it, or is the title strictly a `Sidebar`-level concern?

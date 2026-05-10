---
node_id: concorda-web::src/app/members/layout.tsx::DashboardLayout
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d3dc18efb6923f187f46100b7a1e7680a6f8e8436c26eaf01f26ca53697ed596
status: llm_drafted
---

# DashboardLayout

## Purpose

The primary layout wrapper for all authenticated member routes. It provides the structural scaffolding for the dashboard, including the `SidebarProvider`, responsive mobile header, and the `SidebarInset` container. It is responsible for determining the dynamic `sectionTitle` based on the current pathname to ensure the mobile top bar reflects the user's current location (e.g., "Inbox" or "Crew & Boat Finder").

## Invariants

- **Requires Authentication**: The layout relies on `useAuth()` to guard the view. If `isLoading` is true or `isAuthenticated` is false, it renders a full-screen `Loader2` spinner.
- **Responsive Header**: The mobile-only header (visible below `md` breakpoint) is a hard-coded part of this layout and must contain the `SidebarTrigger` and `sectionTitle`.
- **Sidebar Sync**: Uses `SidebarBreakpointSync` to ensure sidebar state remains consistent across viewport changes.
- **Layout Nesting**: All children are wrapped in `SidebarInset` to ensure correct overflow and scrolling behavior within the sidebar-driven architecture.

## Gotchas

- **Mobile Scroll Locking**: Per commit `c366645`, the layout must maintain `overflow-y-auto` and `overflow-x-hidden` on the `main` element, and `min-w-0` on `SidebarInset` to prevent horizontal scroll breakage on mobile devices.
- **Header Visibility**: The mobile header is explicitly hidden on desktop via `md:hidden`. If adding a new global mobile element, ensure it is placed within the `header` tag in this layout rather than the individual page components.
- **Auth Redirects**: This component does not perform the redirect itself; it only renders the loading state. The actual redirection logic is handled by the `AuthProvider` (see `useAuth` implementation).

## Cross-cutting concerns

- **Auth**: Dependent on `useAuth()`. The layout acts as a visual gatekeeper, showing a loader until authentication state is resolved.
- **Side effects**: The `sectionTitle` logic affects the mobile top bar visibility for all sub-routes like `/members/inbox` and `/members/finder`.

## External consumers

None known.

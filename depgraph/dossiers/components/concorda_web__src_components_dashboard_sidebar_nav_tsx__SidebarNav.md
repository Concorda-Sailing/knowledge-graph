---
node_id: concorda-web::src/components/dashboard/sidebar-nav.tsx::SidebarNav
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3f50e51adc1e36b993f4626fc179dfa3320744a4ba778a818d7d2a4e9c882cb3
status: llm_drafted
---

# SidebarNav

## Purpose

The primary navigation component for the dashboard layout. It provides the main vertical navigation links (Awards, Fleets, Rules, etc.) and displays the authenticated user's profile information, including their avatar and name. It is designed to handle both desktop (expanded/collapsed) and mobile (drawer) states via the `useSidebar` hook.

## Invariants

- **Mobile behavior**: On mobile devices, clicking any `Link` must trigger `closeOnMobile` to call `setOpenMobile(false)`, preventing the drawer from remaining open over the new page content.
- **Profile data fetching**: The component fetches the user's `picture_url` via `profileApi.get()` on mount.
- **Fallback UI**: If the profile picture fails to load or is null, the component must show an `AvatarFallback` containing the user's initials or a "?" string.
- **Collapsible state**: When the sidebar is in `icon` mode, the brand/logo and the user's full name/avatar are visually condensed or hidden to maintain layout integrity.

## Gotchas

- **Mobile drawer persistence**: Per commit `6bb024e`, links must explicitly call `closeOnMobile` on click; otherwise, the drawer stays open on mobile, obscuring the destination page.
- **Layout centering**: Per commit `b839793`, the user avatar and name require specific CSS/group-data logic to ensure they center correctly when the sidebar is in the collapsed/icon state.
- **Brand visibility**: Per commit `79f4037`, the brand/logo block must be explicitly hidden via `group-data-[collapsible=icon]:hidden` when the sidebar is collapsed to prevent layout overflow.

## Cross-cutting concerns

- **Auth**: Relies on `useAuth()` to retrieve the current user's name and initials.
- **Side effects**: The `InboxNavItem` (imported) may display real-time unread counts or badges based on the user's inbox state.

## External consumers

None known.

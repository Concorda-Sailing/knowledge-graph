---
node_id: concorda-web::src/components/dashboard/dashboard-tabs-list.tsx::DashboardTabsList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 36676f7648d8a410bbf4df5c7ef1fbdc0d743f196325905fa3a66776cc66844f
status: current
---

# DashboardTabsList

## Purpose

The `DashboardTabsList` component renders the primary navigation bar for the user dashboard. It manages the visibility of various navigation triggers (Get Started, My Schedule, Boats, My Crew, and My Profile) based on user state and permissions. It is used to provide high-level navigation and visual cues (badges) for pending actions or missing information.

## Invariants

- **`isBoatOwner` controls visibility** — The "My Crew" tab is only rendered if `isBoatOwner` is true.
- **`showGetStarted` controls visibility** — The "Get Started" tab is only rendered if `showGetStarted` is true.
- **Badges use `destructive` variant** — Both `pendingInviteCount` and `profileMissing` use the `destructive` variant for high visibility.
- **Absolute positioning for badges** — Badges are positioned with `-top-1.5 -right-1.5` relative to the `TabsTrigger` to ensure they overlap the edge correctly.

## Gotchas

- **Visual prominence** — Per commit `2627d27`, the active tab uses the `ACTIVE_TAB_PROMINENT` class to ensure the user knows which section they are currently viewing.
- **Responsive sizing** — The component uses `text-xs md:text-sm` and specific padding (`px-2 md:px-3`) to ensure the tabs remain usable on mobile devices without breaking the layout.

## Cross-cutting concerns

- **Auth**: Visibility of "My Crew" is dependent on the `isBoatOwner` prop, which is derived from user permissions.
- **Side effects**: The `pendingInviteCount` badge provides a visual cue for the "My Schedule" tab, and `profileMissing` provides a cue for the "My Profile" tab.

## External consumers

None known.

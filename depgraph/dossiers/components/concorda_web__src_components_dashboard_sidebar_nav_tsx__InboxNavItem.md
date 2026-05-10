---
node_id: concorda-web::src/components/dashboard/sidebar-nav.tsx::InboxNavItem
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7bebd5262949c009ba48671321e35010c7ec7a76bd1c4d721d548dc7ec41f78d
status: current
---

# InboxNavItem

## Purpose

The `InboxNavItem` is a specialized sidebar navigation component that displays a real-time notification badge for pending user actions. It aggregates counts from three distinct sources: pending approvals, outgoing-related notifications, and crew requests. Use this component when you need to provide a high-level summary of "pending attention" items in the sidebar, rather than a generic navigation link.

## Invariants

- **Aggregated Count**: The badge displays the sum of `incoming.length`, `outgoing.length`, and `crewRequests.length`.
- **Conditional Rendering**: The `Badge` component only renders if the total `count` is greater than 0.
- **Responsive Visibility**: The badge uses `group-data-[collapsible=icon]:hidden` to ensure the count is hidden when the sidebar is in its collapsed/icon-only state.
- **Navigation Trigger**: The component relies on an `onNavigate` prop to handle the transition to the `/members/inbox` route.

## Gotchas

- **Badge visibility in collapsed mode**: Per commit `79f4037`, the badge is explicitly hidden via CSS classes when the sidebar is collapsed to prevent layout breakage/overflow in the icon-only view.
- **Data source dependency**: The count is derived from `usePendingApprovals` and `useInboxCrewRequests`. If these hooks are not properly context-aware or are mocked incorrectly in tests, the badge count will be inaccurate.
- **Recent feature expansion**: Per commit `be6b4d5`, this component was recently updated to include "pending crew requests" in the total count; ensure any logic involving the "Inbox" count accounts for this third source.

## Cross-cutting concerns

- **Auth**: Relies on the user's session-based permissions to populate the `usePendingApprovals` and `useInboxCrewRequests` hooks.
- **Side effects**: The presence of a non-zero count serves as a visual indicator for the user to check the Inbox, affecting the perceived urgency of pending crew or approval tasks.

## External consumers

None known.

---
node_id: concorda-web::src/components/dashboard/sidebar-admin.tsx::SidebarAdmin
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 965f4798d8c5a36e4291ed02c01a0bf0edd1c17820d66e15c0695c6f70c7e2a3
status: llm_drafted
---

# SidebarAdmin

## Purpose

The `SidebarAdmin` component renders the administrative section of the dashboard sidebar. It provides navigation links to high-level organization management tools (Email, SMS, WhatsApp, Payments, etc.) and uses a permission-based filtering system to ensure users only see links they are authorized to access. It is distinct from the standard user sidebar by including specific `adminOrgItems` and `adminEmailItems` that are gated by the `user.permissions` array.

## Invariants

- **Permission-gated visibility**: Items in `adminOrgItems` are filtered by `user?.permissions?.includes(item.permission)`. If a user lacks the specific permission string, the link is omitted from the DOM.
- **Path-based active states**: `SidebarMenuButton` uses `pathname.startsWith(item.href)` to determine the `isActive` state, ensuring the sidebar reflects the current sub-route.
- **Collapsible state synchronization**: The `defaultOpen` prop for `Collapsible` components is driven by the current `pathname` to ensure sub-menus (like Email templates) are expanded when navigating via direct URL.

## Gotchas

- **Permission-based visibility is client-side**: While the UI hides links via the `.filter()` on `adminOrgItems`, the actual security is enforced by the API. A user could theoretically navigate to `/members/admin/llm` if they know the URL, but the `useAuth` hook and subsequent page components must handle the unauthorized state.
- **Recent expansion of admin surface**: Per commit `37794d5`, the admin area now includes health/pool stats. Ensure any new admin links added to the sidebar are also reflected in the corresponding route/page components to avoid "dead" links.

## Cross-cutting concerns

- **Auth**: Uses `useAuth()` to access `user.permissions` for rendering the menu items.
- **Side effects**: Changes to the navigation structure here affect the visibility of administrative routes like `/members/admin/email/compose` and `/members/admin/system`.

## External consumers

None known.

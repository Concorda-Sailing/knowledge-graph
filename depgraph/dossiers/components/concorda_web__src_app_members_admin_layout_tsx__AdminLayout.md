---
node_id: concorda-web::src/app/members/admin/layout.tsx::AdminLayout
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 49d23cc79cd01da1c7cc8ae6b729234c59d2cb744407c04113636e534d930ff7
status: llm_drafted
---

# AdminLayout

## Purpose

The `AdminLayout` component acts as a client-side guard for the administrative sub-routes within the members section. It wraps protected children in a permission-check layer that verifies if a user possesses either a broad `admin.` permission or specific event management capabilities. It is distinct from a global auth guard because it specifically targets roles like `event_manager` or `delegate` that are not necessarily full system admins.

## Invariants

- **Requires `useAuth` context.** The component relies on the `user` object and `isLoading` state from the auth provider.
- **Permission-based access.** Access is granted if the user has any permission starting with `admin.` OR specifically `events.create`, `events.edit`, or `events.delete`.
- **Returns `null` during loading.** To prevent flickering of the "Access Denied" UI, the component returns `null` while `isLoading` is true.
- **Client-side only.** As a `"use client"` component, it performs the permission check in the browser; it does not replace server-side route protection.

## Gotchas

- **Broad permission match.** The use of `p.startsWith("admin.")` means any new permission added to the schema that begins with this prefix will automatically grant access to this layout.
- **Implicit role elevation.** Because `events.create`, `events.edit`, and `events.delete` grant access to the entire admin layout, users with these specific event permissions can see all admin sub-routes (like `AnalyticsPage` or `ErrorLogPage`) unless those pages implement their own more granular guards.

## Cross-cutting concerns

- **Auth**: Depends on `useAuth` to provide the `user.permissions` array.
- **Side effects**: Protects all sibling routes in the `/members/admin/` directory, including `AdminClubsPage`, `SeriesPage`, and `AnalyticsPage`.

## External consumers

None known.

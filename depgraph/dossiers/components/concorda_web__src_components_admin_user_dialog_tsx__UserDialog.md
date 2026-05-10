---
node_id: concorda-web::src/components/admin/user-dialog.tsx::UserDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d844b626e006a1b16780546989aa4d58098ee1bff7737c6a2cf91ef98f43de62
status: current
---

# UserDialog

## Purpose

A modal dialog used for creating or editing user profiles within the admin dashboard. It handles the state transition between "Add Mode" (empty form) and "Edit Mode" (populated with existing user data). It is the primary interface for managing user-specific settings like directory opt-ins, roles, and product memberships.

## Invariants

- **`userId` determines mode**: If `userId` is present, the component enters edit mode and fetches existing user data via `adminApi.getUser(userId)`.
- **Form reset on close**: The form state is reset when `open` is false or when transitioning from edit mode to add mode to prevent stale data leakage.
- **Phone number formatting**: Uses `formatPhoneNumber` from `@/lib/utils` to ensure the input string matches the expected database format during the edit lifecycle.
- **Role and Product loading**: Roles and active membership products are fetched on mount to populate the selection options.

## Gotchas

- **Mobile layout constraints**: Per commit `0564f06`, the dialog must cap its width and stack the footer on `<md` (medium) breakpoints to prevent broken layouts on smaller screens.
- **Form reflow issues**: Per commit `019f6e3`, the form layout must handle single-column reflow for mobile devices to avoid horizontal scrolling in admin grids.
- **Password field visibility**: Per commit `f0c5e0d`, the dialog includes logic to show/hide the password field, which is critical for UX when editing existing users where the password might be left blank.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges to call `adminApi.getUser` and `rolesApi.list`.
- **Side effects**: Updates to this dialog (specifically `product_ids` and `roles`) impact the user's membership status and access levels across the platform.

## External consumers

None known.

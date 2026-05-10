---
node_id: concorda-web::src/components/admin/settings-page.tsx::SettingsPageInner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ba103e7d333cae8a01883df0f0ced268afb6ff8fbaeb4d181945d1be373c288b
status: llm_drafted
---

# SettingsPageInner

## Purpose

Provides a standardized layout wrapper for administrative settings views. It handles the visual transition between loading states (using either a centered `Loader2` spinner or a `useSkeleton` layout) and the final content. The `SettingsPage` export acts as a permission-aware wrapper, while `SettingsPageInner` is the functional core used for rendering the actual title, subtitle, and action buttons.

## Invariants

- **`useSkeleton` determines loading UI**: If `true`, it renders a vertical stack of `Skeleton` components; if `false` or undefined, it renders a centered `Loader2` spinner.
- **`actions` placement**: The `actions` prop is rendered in a flex container to the right of the title/subtitle header.
- **`title` and `subtitle` hierarchy**: The component expects a `title` (h1) and a `subtitle` (p) to maintain consistent typography across the admin dashboard.
- **`permission` wrapping**: The `SettingsPage` component uses `PermissionGate` to wrap the inner content if a permission string is provided.

## Gotchas

- **Layout shift on loading**: Switching `useSkeleton` from `true` to `false` causes a significant layout shift because the `Loader2` is wrapped in a `justify-center` flex container, whereas the skeleton is a `space-y-6` stack.

## Cross-cutting concerns

- **Auth**: Uses `PermissionGate` when a `permission` prop is passed to the `SettingsPage` wrapper.
- **Side effects**: Part of the "admin layout refresh" (commit `7a47845`) intended to standardize the look of admin-facing configuration pages.

## External consumers

None known.

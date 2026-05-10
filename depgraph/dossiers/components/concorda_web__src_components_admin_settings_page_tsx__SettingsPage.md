---
node_id: concorda-web::src/components/admin/settings-page.tsx::SettingsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9c91b0d06f19a382b19a606fc24a55722353cb2e10bfa705ea1526c6f0045230
status: llm_drafted
---

# SettingsPage

## Purpose

The `SettingsPage` component serves as the top-level container for administrative settings views. It provides a standardized layout (header, subtitle, and actions) and acts as a conditional wrapper that enforces access control via the `PermissionGate`. An agent should use this component when creating new administrative sub-pages to ensure consistent layout and to wrap the view in the necessary permission logic.

## Invariants

- **Permission-based rendering**: If the `permission` prop is provided, the content is wrapped in a `<PermissionGate>`.
- **Layout consistency**: The component manages the header area, including the `subtitle` and the `actions` slot.
- **Prop forwarding**: All properties not explicitly handled by the signature are passed through to `SettingsPageInner` via `...props`.

## Gotchas

- **Layout refresh requirements**: Per commit `7a47845`, this component is part of the "admin layout refresh" and is used to surface new administrative components like the invited-crew view. Changes to the header or spacing here will propagate to all admin settings sub-views.

## Cross-cutting concerns

- **Auth**: Uses `<PermissionGate>` to gate access based on the provided `permission` string.
- **Side effects**: Serves as the layout shell for administrative sub-pages (e.g., user management, club settings).

## External consumers

None known.

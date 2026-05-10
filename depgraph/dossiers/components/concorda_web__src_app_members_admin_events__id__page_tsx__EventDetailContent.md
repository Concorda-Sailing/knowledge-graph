---
node_id: concorda-web::src/app/members/admin/events/[id]/page.tsx::EventDetailContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6dedeb81a547c9cbdc81f24a36f0f07ea81694db11d37ce63eab79d612c04dbe
status: current
---

# EventDetailContent

## Purpose

The core UI engine for the event management interface. It handles the dual-mode logic for both creating a "new" event and editing an existing one, managing complex state for event metadata, image uploads, ticket/product configurations, and registration lists. It is wrapped by `PermissionGate` in the parent component to ensure only authorized admins can access the form.

## Invariants

- **Mode-driven state**: The `mode` state determines if the component is in `"new"` or `"view"` mode, which dictates whether `eventData` is populated or if `formData` is initialized as a blank template.
- **Category-driven navigation**: The `backUrl` is dynamically calculated based on whether the event category is `"regatta"` or `"social"`, ensuring the user returns to the correct administrative dashboard.
- **Slug management**: `slugManuallyEdited` tracks if the user has overridden the auto-generated slug to prevent accidental overwrites during save operations.
- **Error scrolling**: The `errorRef` is used to programmatically scroll the viewport to the error message when `error` state is non-null.

## Gotchas

- **Mobile layout reflow**: Per commit `019f6e3`, admin-level forms and grids require specific single-column reflows on mobile to prevent layout breaking.
- **Dialog width constraints**: Per commit `0564f06`, any new dialogs or nested forms added to this component must respect the `max-width` and stack footer constraints to avoid breaking the mobile experience.
- **Type safety for event types**: Recent changes (commit `f1fcabf`) introduced specific datetime and form conversion helpers; ensure any new form fields for dates use the established org-timezone conversion patterns to avoid the "naive datetime" issues seen in previous versions.

## Cross-cutting concerns

- **Auth**: Protected by `PermissionGate` with `["events.create", "events.edit", "events.view"]`.
- **Side effects**: Changes to event data (name, category, or slug) directly impact the visibility and routing of the "back" navigation for the admin dashboard.

## External consumers

None known.

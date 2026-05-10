---
node_id: concorda-web::src/components/admin/detail-page-header.tsx::DetailPageHeader
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c6536c32f39eca61dfce5c1cc38264485817c94ac4afd1cba5dd0dddb99bc6a2
status: current
---

# DetailPageHeader

## Purpose

The standard header component for administrative detail views. It provides a consistent navigation pattern consisting of a back button (with a custom label) and a page title, alongside an optional slot for contextual action buttons (e.g., Edit, Delete, or Save). Use this instead of manual `flex` layouts when building a sub-page for an entity to ensure the "back" navigation and title alignment remain uniform across the admin dashboard.

## Invariants

- **`backHref` is required.** The component relies on a valid string to prevent broken navigation paths.
- **`backLabel` is required.** The back button must always display text to ensure accessibility and clear intent.
- **`actions` is optional.** If not provided, the right-side container is not rendered, preventing unnecessary whitespace.

## Gotchas

- **Layout spacing.** The component uses `gap-3` for the left-side elements and `gap-2` for the actions. If adding complex nested components to the `actions` prop, ensure they do not break the `flex-center` alignment.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.

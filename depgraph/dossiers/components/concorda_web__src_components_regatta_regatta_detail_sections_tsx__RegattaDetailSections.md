---
node_id: concorda-web::src/components/regatta/regatta-detail-sections.tsx::RegattaDetailSections
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b045e1e2bd3adc8a1f47e99d95a3409842277e7d719734b1fc1e4068b4b49f24
status: current
---

# RegattaDetailSections

## Purpose

The primary display component for a regatta's metadata and administrative details. It organizes high-level links (NOR, SI, Registration), technical race details (First Warning, RC Channel, Course), and descriptive content into a structured layout. It is used to provide a consistent "at-a-glance" view of a regatta's logistics within the detail view.

## Invariants

- **Uses `LinkSlot` for external resources.** Links like `nor_url` and `si_url` must be wrapped in `LinkSlot` to ensure the `authed` prop is respected for protected documents.
- **Requires a `regatta` object of type `RegattaDetail`.** The component expects a fully populated object; missing keys like `classes` or `qualifiers` are handled via empty array fallbacks to prevent runtime errors.
- **`classDisplayName` formatting.** The helper function `classDisplayName` must be used to combine `name` with `sail_type` or `fleet_designator` to ensure consistent string representation in the UI.
- **Uses `<Dash />` for null/empty values.** Any field that is empty or null (e.g., `max_races`, `description`) must render the `<Dash />` component rather than an empty string or `null` to maintain layout stability.

## Gotchas

- **Timezone consistency.** Per commit `f444b4c`, all datetime-related data rendered within these sections (or passed to sub-components) must be rendered in the organization's timezone, not the browser's local time.
- **Layout hierarchy.** Per commit `3aada74`, the "Documents & Links" row (NOR, SI, Registration, Site) is intentionally placed at the top of the section to prioritize access to official documents.

## Cross-cutting concerns

- **Auth**: Uses `authed` prop on `LinkSlot` for sensitive links like NOR and SI.
- **Side effects**: Updates to the `regatta` object in the parent view will trigger a re-render of these sections.

## External consumers

None known.

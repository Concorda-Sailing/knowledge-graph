---
node_id: concorda-web::src/components/ui/badge.tsx::Badge
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2224245fe728a01282aec4473f3f096be8659adf591792ccb698b2d76d745d01
status: current
---

# Badge

## Purpose

A low-level UI component used to display status indicators, tags, or labels. It wraps a `div` with styling driven by the `badgeVariants` function. Use this for high-level status indicators (e.g., "Active", "Pending") rather than building custom inline spans, to ensure consistent padding and color-coding across the dashboard.

## Invariants

- **Base element is a `div`** — The component renders a `div` by default, not a `span`.
- **Extends standard HTML attributes** — It accepts all standard `HTMLDivElement` props, including `className` and `style`.
- **Variant-driven styling** — Visual appearance is controlled via the `variant` prop, which maps to the `badgeVariants` definition.

## Gotchas

- **Commit `4d41ba6`** — This component was part of the initial full web application rollout (dashboard, admin, auth, profile). As a foundational UI element, any changes to its base `badgeVariants` will propagate to all status indicators across the new dashboard and admin views.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.

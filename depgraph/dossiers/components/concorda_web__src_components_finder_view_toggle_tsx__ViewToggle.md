---
node_id: concorda-web::src/components/finder/view-toggle.tsx::ViewToggle
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 32c58515443f28f1825486d5dcc8c5d4da4a406b6ae610f03df8b3a0cbb25b96
status: current
---

# ViewToggle

## Purpose

A UI toggle component used to switch between "grid" and "list" display modes within the finder interfaces. It provides two icon-based buttons that act as a control switch for the layout of the parent container. Use this when a finder view requires a layout-agnostic way to switch between dense list views and visual grid views.

## Invariants

- **Strict view types**: The `view` prop must be exactly `"grid"` or `"list"`.
- **Controlled component**: The component does not manage its own state; it relies entirely on `onViewChange` to propagate changes to the parent.
- **Button styling**: The active view is indicated by the `default` variant, while the inactive view uses the `outline` variant.

## Gotchas

- **Accessibility requirements**: Per commit `5dc460a`, buttons must include `aria-label` attributes ("Grid view" and "List view") to ensure screen readers can identify the toggle intent.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Triggers layout re-renders in parent components like `BoatFinderPanel` or `CrewFinderPanel` via the `onViewChange` callback.

## External consumers

None known.

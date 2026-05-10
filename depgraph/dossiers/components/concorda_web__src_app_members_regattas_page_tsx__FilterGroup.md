---
node_id: concorda-web::src/app/members/regattas/page.tsx::FilterGroup
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9572d8836e9ca88fb97751b1be46d007e8e49255ed0e32fa58d46e7027f5d128
status: llm_drafted
---

# FilterGroup

## Purpose

A stateless UI component used to render a labeled group of selectable filter buttons. It provides a standardized way to toggle items within a `Set<string>` and includes a "Clear" action to reset the selection. It is used within the `RegattasPage` to manage multiple filter categories like regions, clubs, and types.

## Invariants

- **`options` length check**: If `options.length === 0`, the component returns `null` and renders nothing.
- **`selected` type**: The `selected` prop must be a `Set<string>` to support the `.has()` and `.size` checks used for rendering.
- **`onToggle` signature**: The callback must accept a single `string` representing the value of the clicked button.
- **`renderLabel` optionality**: If provided, this function transforms the raw option string into a display-friendly format (e.g., for abbreviations or localized text).

## Gotchas

- **Manual state management required**: This component is purely presentational; it does not manage its own state. The parent must handle the `Set` updates and ensure the `onToggle` function correctly mutates or replaces the state in the parent's scope.
- **Button type defaults**: Buttons are explicitly set to `type="button"` to prevent accidental form submissions if the `RegattasPage` is ever wrapped in a `<form>` element.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the visibility of regatta lists in the `RegattasPage` via the `selected` state.

## External consumers

None known.

---
node_id: concorda-web::src/components/ui/save-bar.tsx::SaveBar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b5d69b4d0623acd5f277aff9c0b3b11267906b6f9b9d3bd490230d7a585e0d27
status: llm_drafted
---

# SaveBar

## Purpose

A fixed-position UI component used to display a "Save" action and status feedback (saving, success, or error notes) at the bottom of the viewport. It is designed to be used in forms or settings pages where a persistent action bar is required. It dynamically adjusts its horizontal offset based on the `useSidebar` state to ensure it doesn't overlap or get hidden by the sidebar when it is expanded.

## Invariants

- **Positioning is relative to the sidebar.** The `left` style property must be driven by `sidebarWidth` (calculated via `useSidebar`) to prevent the bar from being obscured by the navigation.
- **`disabled` state is additive.** The button is disabled if either the `saving` prop is true OR the `disabled` prop is true.
- **`type` defaults to `"submit"`.** This allows it to be used within a `<form>` as the primary submit button without extra configuration.
- **`label` defaults to `"Save Changes"`.**

## Gotchas

- **Z-index collision.** The component uses `z-[5]`, which is relatively low. If a modal or a high-index dropdown is active, this bar may be rendered behind it.
- **Layout shift on mobile.** The `sidebarWidth` calculation assumes a mobile-friendly layout, but if `isMobile` is not correctly handled by the parent context, the `left` offset may cause the bar to jump or overlap content.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/- The `onSave` callback is typically the trigger for audit-logged mutations in parent components.
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.

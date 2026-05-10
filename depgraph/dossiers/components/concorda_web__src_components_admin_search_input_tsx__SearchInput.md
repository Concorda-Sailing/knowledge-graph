---
node_id: concorda-web::src/components/admin/search-input.tsx::SearchInput
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4ea328ef0025c53af79cb96e705a727d2d4d4eb9d192c92d4ffbd8ae4980e610
status: llm_drafted
---

# SearchInput

## Purpose

A specialized input component for admin-facing search fields. It wraps a standard UI `Input` with a hardcoded magnifying glass icon (`Search`) and specific padding to ensure visual consistency across the admin dashboard. Use this instead of a raw `Input` when building search bars for lists to maintain the standard `pl-10` left-padding and icon alignment.

## Invariants

- **Controlled Component**: The `value` and `onChange` props must be managed by the parent component to ensure the input remains a controlled component.
- **Visual Layout**: The icon is absolute-positioned with `left-3 top-1/2 -translate-y-1/2`, requiring the input text to have `pl-10` to prevent text overlap.
- **Default Dimensions**: The component defaults to `flex-1 min-w-[200px] max-w-sm` unless overridden via the `className` prop.

## Gotchas

- **Icon Dependency**: The component relies on the `Search` icon from the local icon library; if the icon set is updated or changed, this component's visual identity changes.
- **Recent Addition**: Introduced in commit `b6ca664` as part of the admin-list-page feature set; it is a relatively new primitive in the admin module.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.

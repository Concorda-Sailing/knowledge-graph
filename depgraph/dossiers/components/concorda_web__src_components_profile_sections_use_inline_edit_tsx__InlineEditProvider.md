---
node_id: concorda-web::src/components/profile/sections/use-inline-edit.tsx::InlineEditProvider
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fdf190f57bdbfa32cc485779b02ccb9944589704a6635a95361ca3241dbdf4b4
status: current
---

# InlineEditProvider

## Purpose

Provides the context provider and hook for managing inline editing states within profile sections. It abstracts the orchestration of `beginEdit`, `cancelEdit`, and `saveEdit` actions, allowing individual profile components to register their forms via `registerForm` without managing the global editing state themselves. Use this when a component needs to participate in a "click-to-edit" flow that requires a single source of truth for which section is currently active.

## Invariants

- **Requires a provider.** `useInlineEdit` will throw a runtime error if called outside of an `InlineEditProvider`.
- **`section` is required for hook calls.** The `useInlineEdit` hook requires a specific `EditingSection` to be passed in to determine if that specific section is the one currently being edited.
- **`registerForm` is a higher-order function.** It accepts a `key` and returns a function that accepts a `FormHandle` to facilitate the registration of form-specific control logic.

## Gotchas

- **Introduced in commit `3641112`.** This is a relatively new pattern for section extraction in the profile; older components in the profile may still be using local state or different patterns for editing.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Used by profile sections (e.g., `SecuritySection`, `SailingExperienceSection`) to manage the transition between read-only and edit modes.

## External consumers

None known.

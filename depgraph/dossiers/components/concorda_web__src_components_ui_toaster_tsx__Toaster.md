---
node_id: concorda-web::src/components/ui/toaster.tsx::Toaster
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0b93b2b60da3f24233700ded66c1e5efe695ab5a6964e51e7b502a8da2664901
status: llm_drafted
---

# Toaster

## Purpose

The global container for rendering toast notifications. It wraps the `ToastProvider` and maps the active `toasts` array from the `useToast` hook into visible UI elements. This component must be placed at a high level in the component tree (usually in the root layout) to ensure notifications are visible regardless of the current route or view.

## Invariants

- **Requires `ToastProvider` context.** The `Toaster` component provides the `ToastProvider` wrapper, ensuring all children have access to the toast state.
- **Uses `useToast` for state.** It relies on the `toasts` array provided by the hook to determine what to render.
- **Iterates via `id`.** The `key` prop for each toast is the unique `id` from the toast object to ensure stable React reconciliation.
- **Prop-drilling via `{...props}`.** The component spreads remaining props onto the `Toast` component, allowing for custom styling or behavior passed from the trigger.

## Gotchas

- **Single instance requirement.** Per commit `4d41ba6`, this is part of the initial full web application setup; if multiple `Toaster` components are mounted, toast state may become desynchronized or multiple providers may conflict.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.

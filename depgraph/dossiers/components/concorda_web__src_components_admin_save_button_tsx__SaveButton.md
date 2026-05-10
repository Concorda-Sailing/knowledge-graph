---
node_id: concorda-web::src/components/admin/save-button.tsx::SaveButton
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 779188ffc26083af5b225d4890530ce68466f3485e5a13514449869b6ddde374
status: current
---

# SaveButton

## Purpose

A specialized UI button used in admin configuration forms to indicate the lifecycle of an asynchronous save operation. It provides visual feedback by switching between a standard action icon, a loading spinner, and a success checkmark based on the current state of the request.

## Invariants

- **`disabled` state is additive.** The button is disabled if either the `disabled` prop is true OR if `saving` is true.
- **`saving` prop takes precedence over `saved`.** If `saving` is true, the component renders the `Loader2` icon regardless of the `saved` state.
- **`label` is a fallback.** The button displays the `label` prop unless `saved` is true, in which case it displays "Saved".

## Gotchas

- **Visual state mismatch.** Because `saving` takes precedence, if a developer triggers a save but fails to set `saving={true}` immediately, the user may see the old label/icon during the latency-heavy start of the request, leading to double-clicks.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: Used in admin layout components (e.g., `invited-crew` surface) to manage configuration persistence state.

## External consumers

None known.

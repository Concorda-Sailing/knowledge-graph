---
node_id: concorda-web::src/components/profile/boats-list.tsx::BoatsList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 11006310e28655d7ccc1e5c24c0706f76b0159935ee6165cb1cc994659cce651
status: llm_drafted
---

# BoatsList

## Purpose

Renders a list of boats associated with the authenticated user's profile. It provides an interface for adding new boats via a dialog and deleting existing ones. It is distinct from a pure display component because it manages local state for deletion and addition-in-progress, and it relies on `profileApi` for direct mutations.

## Invariants

- **Uses `profileApi.deleteBoat(id)` for removal.** Deletion is an asynchronous operation that must be awaited before updating the local `onUpdate` state.
- **Requires `onUpdate` to refresh parent state.** After a successful `deleteBoat` or `getBoats` call, the component calls `onUpdate` with the fresh list to ensure the UI stays in sync with the server.
- **`onUpdate` is the single source of truth for the list.** The component does not maintain the master list; it receives it via props and propagates changes back up.

## Gotchas

- **Inline boat detail requirement:** Per commit `a29494e`, the dashboard now requires inline boat details; ensure any changes to the boat object structure account for the "duration" requirement mentioned in that commit.
- **Dialog state management:** The `setDeleting(true)` state is used to prevent multiple concurrent delete attempts, but it only covers the `handleDeleteConfirm` flow.

## Cross-cutting concerns

- **Auth**: Uses `profileApi` which requires an authenticated session.
- **Side effects**: Triggers `onUpdate` which refreshes the boat list in the parent component (likely the Profile dashboard).

## External consumers

None known.

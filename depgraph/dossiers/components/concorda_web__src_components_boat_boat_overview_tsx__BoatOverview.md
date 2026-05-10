---
node_id: concorda-web::src/components/boat/boat-overview.tsx::BoatOverview
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3c9ddd4a9cda00c87f63878c2cec24147c7a76291c8c2282e04fc51dff9b3f2e
status: llm_drafted
---

# BoatOverview

## Purpose

Displays the high-level summary and administrative controls for a boat. It acts as a container for the `BoatPublishBar` when the user has owner privileges, allowing them to manage the boat's public visibility/resume status. Use this component when you need to present a unified view of boat metadata and owner-specific actions in a single layout block.

## Invariants

- **`isOwner` must be true for the `BoatPublishBar` to render.** If `isOwner` is false or `onResumeUpdate` is not provided, the administrative card is entirely omitted from the DOM.
- **`resume` is optional.** The component handles `resume ?? null` to ensure the `BoatPublishBar` receives a valid object or null, preventing crashes on uninitialized state.
- **`onUpdate` is a required callback for owner actions.** The component relies on this function to propagate changes from the `BoatPublishBar` back up to the parent state/store.

## Gotchas

- **Dashboard overhaul dependency:** Per commit `76ad44e`, this component is part of the "Dashboard overhaul" which includes inline boat configuration and drag-drop photo management. Changes to the layout here may impact the visual density of the owner's dashboard.
- **Prop drilling for `onResumeUpdate`:** If the parent component fails to pass the update handler, the `BoatPublishBar` will be hidden even if `isOwner` is true, due to the `isOwner && onResumeUpdate` guard.

## Cross-cutting concerns

- **Auth**: Depends on `isOwner` prop, which is typically derived from the user's role/permissions in the parent view.
- **Side effects**: Updates to the `BoatResume` via the internal `BoatPublishBar` will trigger the `onResumeUpdate` callback, affecting the boat's public-facing profile.

## External consumers

None known.

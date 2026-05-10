---
node_id: concorda-web::src/components/dashboard/my-crew-tab.tsx::SortableCrewCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d7aea9213b5993fd34469bf1b568022b294dde3e62cc685bffe7c9b75790c31d
status: current
---

# SortableCrewCard

## Purpose

A specialized wrapper for `CrewMiniCard` that implements drag-and-drop functionality via `@dnd-kit`. It allows users to reorder their crew members visually. It is distinct from the standard `CrewMiniCard` by adding a `GripVertical` handle and managing the `isDragging` visual state.

## Invariants

- **Uses `member.person_uuid` as the sortable ID** to ensure stable identity during drag operations.
- **`onRemove` is conditionally disabled** via the `onRemove` prop if the member's role is `"owner"`, preventing accidental deletion of the primary account holder.
- **`transform` and `transition` styles are applied** to the outer `div` to ensure smooth movement during the drag sequence.
- **The drag handle is a specific sub-element** (the `GripVertical` icon) and is the only part of the card that triggers the `listeners` for drag initiation.

## Gotchas

- **Role-based permission logic:** Per `onRemove={member.role !== "owner" ? onRemove : undefined}`, owners cannot be removed via this UI. This is a critical safety check to prevent accidental loss of boat ownership.
- **Drag activation distance:** The parent `MyCrewTab` uses a `PointerSensor` with an `activationConstraint` of `distance: 5`. This prevents accidental drags when a user intends to click or tap the card.
- **Z-index and pointer events:** The drag handle uses `z-20` and `cursor-grab` to ensure the handle is interactable and doesn't conflict with the card's internal click events.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi.getMyCrew()` to fetch the initial list; the ability to remove members is implicitly tied to the user's permissions to modify their own crew.
- **Side effects**: Reordering this card affects the visual order of the `MyCrewTab` list, but the actual persistence of the new order must be handled by the parent's state-update logic (not shown in this component).

## External consumers

None known.

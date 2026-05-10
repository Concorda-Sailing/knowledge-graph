---
node_id: concorda-web::src/components/dashboard/position-slot-grid.tsx::PositionSlotGrid
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5906b4bc87f7f0ded164228adb6bd1fa7890f6a8d788563922b67cd1230bcbad
status: llm_drafted
---

# PositionSlotGrid

## Purpose

Renders a visual grid of position slots (e.g., Skipper, Bow, etc.) for an event, allowing users to view current assignments and interact with them. It supports two distinct modes: "Self-Assign" mode (where a user can claim an open slot) and "Owner Mode" (where an owner can assign specific crew members via a popover). Use this component when you need a compact, circular-button representation of crew positions that handles both mobile tap-to-reveal interactions and desktop hover states.

## Invariants

- **`slots` must be an array of objects with a `name` property.** The `name` is used as the key for lookups in the `positionAssignments` Map.
- **`positionAssignments` is a Map.** The keys used for look-up must be the stringified index of the slot (e.g., `ec = positionAssignments.get("${i}")`) to ensure alignment between the `slots` array and the assignment data.
- **`onOwnerAssign` triggers Owner Mode.** If `onOwnerAssign` is provided, the component switches from a "claim" interaction to an "assign" interaction, and the internal `onClick` for the button is bypassed to let the parent's popover handle the event.
- **`isMe` check relies on `currentUserId`.** The component calculates `myPosition` by searching the `positionAssignments` Map for the `currentUserId`.

## Gotchas

- **Mobile "Tap-to-reveal" logic.** To prevent accidental clicks on mobile, the "Clear" (X) button is hidden by default and only revealed when a slot is tapped (`setTappedSlotIdx`). This was implemented to handle the lack of hover states on touch devices (see commit `3b0268b`).
- **Aria-label dependency.** The `aria-label` is dynamically generated based on whether the slot is empty, owned, or claimed. If the label logic is broken, screen readers will not correctly communicate the "Claim" or "Assign" intent.
- **Key stability.** Per commit `0b65b73`, the component relies on stable keys and specific index-based lookups to prevent UI flickering when the `positionAssignments` Map updates.

## Cross-cutting concerns

- **Auth**: Behavior changes based on `currentUserId` and whether the user has permission to `onClaim` or `onOwnerAssign`.
- **Side effects**: Changes to these slots typically trigger updates in the parent `ScheduleTab` or `CrewPositionsCard` via the passed-in callback functions.

## External consumers

None known.

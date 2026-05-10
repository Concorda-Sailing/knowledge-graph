---
node_id: concorda-web::src/components/dashboard/event-plan-panel.tsx::EventCrewSlot
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8db715698df58f357b764a51374641a7992000b77bcb5b933390c2d6e2559720
status: llm_drafted
---

# EventCrewSlot

## Purpose

Renders a single visual slot for a crew member within the event planning panel. It displays the person's initials or avatar and uses color-coded rings (emerald for confirmed/accepted, amber for invited, primary for assigned) to indicate the current assignment status. This component is used to visualize the staffing of specific positions for an event.

## Invariants

- **Visual status indicators** — The `ring` color and the `Avatar` opacity are driven by the `assigned.status` string (e.g., `"accepted"`, `"confirmed"`, or `"invited"`).
- **Fallback initials** — If no `eventCrewMember` is assigned, the component renders the `positionInitial(slot.name)` to ensure the slot is not visually empty.
- **Avatar source priority** — The image source prioritizes `assigned.person_picture_url`, falling back to `boatCrewMember?.person_picture_url` if the event-specific person is missing.
- **Assignability logic** — The `assignable` filter (internal to the component's logic) ensures only members without a `position_name` and without a `"declined"` status are eligible for assignment.

## Gotchas

- **Status-based styling** — The visual distinction between a "confirmed" user and an "invited" user is critical for UX; per `f444b4c`, ensure that any status changes (like moving from `invited` to `accepted`) correctly trigger the transition from the `amber-400` ring to the `emerald-500` ring.
- **Avatar fallback** — If `assigned.person_first_name` or `assigned.person_last_name` are missing, the `initials` calculation uses empty strings, which could result in a blank `AvatarFallback`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Updates to this component's state (via `onAssign`/`onUnassign`) affect the visibility of the `EventCrewSlot` within the broader `EventPlanPanel` layout.

## External consumers

None known.

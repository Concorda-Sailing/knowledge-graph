---
node_id: concorda-web::src/components/dashboard/crew-card/available-section.tsx::AvailableSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7e452d0412e3106742b53794a31cb5eb564a541e5ec27df3b14451dd050615fd
status: llm_drafted
---

# AvailableSection

## Purpose

The `AvailableSection` component displays a list of available crew members, categorized by their respective crew pools. It provides a tabbed interface to filter members by pool and allows users to select multiple individuals for invitation. This component is distinct from the assignment logic; it is purely for the selection/discovery phase before a person is officially assigned to a position.

## Invariants

- **Selection order is critical.** The order in which `person_uuids` are added to `selectedOrder` determines the priority for future invite-cap policies (index 0 is highest priority).
- **Input `available` is the source of truth for existence.** If a person is no longer in the `available` array (e.g., they were just invited or moved), they are automatically dropped from the `selectedOrder` via an effect.
- **`onInvite` expects an array of strings.** The function signature requires `(personUuids: string[]) => Promise<void>`.
- **Tabs are dynamic.** The `tabs` array includes an `__all__` tab and one tab per `crewPool` that contains at least one member from the `available` list.

## Gotchas

- **Selection/Availability desync.** Per the logic in the `useEffect` (lines 80-86), if a user is selected but then disappears from the `available` prop, they are purged from the local state. This prevents sending invites to people who are no longer "available" for selection.
- **Sorting is multi-layered.** The component sorts by `priority` first, then by `person_first_name`, and finally by `person_last_name` to ensure a stable, predictable UI order.
- **Tab filtering logic.** The `visible` list is a computed intersection of the `available` members and the `member_ids` within the active `crewPool`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: The `onInvite` callback triggers the actual invitation process, which is a primary driver for the "ordered invite picks" feature mentioned in commit `3b0268b`.

## External consumers

None known.

---
node_id: concorda-web::src/components/dashboard/crew-card/accepted-section.tsx::AcceptedSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8ec01c4ae8719daa1b7a3f2260435ede3d6316452289543ea804f47643275d3c
status: llm_drafted
---

# AcceptedSection

## Purpose

Displays a list of crew members who have already accepted or been confirmed for a race. It provides a collapsible interface to view the current crew and a confirmation dialog to remove members. Use this instead of `AvailableSection` when the user needs to manage members who are already part of the roster.

## Invariants

- **`onRemove` must be awaited.** The `onRemove` prop is a function that returns a `Promise<void>`; the component's internal `doRemove` handler awaits this to manage the `busy` state.
- **`members` must include `person_uuid`.** The component maps over members to render `CrewMiniCard`, which requires the UUID for stable keys and identity.
- **`AlertDialog` is the primary confirmation mechanism.** The `confirm` state holds the member being removed to ensure the correct person is targeted in the `onRemove` call.

## Gotchas

- **Layout spacing.** Per commit `a6d9494`, the section body uses `pt-1` to provide specific spacing between the section header and the expanded member list.
- **Visual styling.** Per commit `1e7e027`, the section uses specific background tints (`bg-emerald-50/40` and `dark:bg-emerald-950/20`) to distinguish the "Accepted" state from other crew sections.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Removing a member via `onRemove` will trigger a re-render of the parent crew-card component.

## External consumers

None known.

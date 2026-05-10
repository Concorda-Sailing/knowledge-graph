---
node_id: concorda-web::src/components/dashboard/crew-card/declined-section.tsx::DeclinedSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9390b6443eb59147eb4745990e797ae8700f741dfd4b1b0c831432bb9d461022
status: current
---

# DeclinedSection

## Purpose

Displays a collapsible list of crew members who have declined an invitation. It acts as a visual separator for the "declined" state within the crew card, providing a high-contrast (red-tinted) UI to distinguish it from the "available" or "accepted" sections. Use this when you need to render a subset of members with a status of `declined` that should not clutter the main view unless explicitly expanded.

## Invariants

- **Input is an array of `CrewMiniCardMember` objects** augmented with a `person_uuid: string`.
- **Initial state is collapsed.** The `collapsed` state defaults to `true` to prevent long lists of declined members from pushing active content off-screen.
- **Uses `XCircle` icon.** The visual identity of the section is tied to the red-themed `XCircle` icon and red background tints.
- **Layout is a flex-wrap container.** The expanded member list uses `flex-wrap` with a `gap-2` to handle varying numbers of members.

## Gotchas

- **Spacing requirements.** Per commit `a6d9494`, there is a specific requirement for `pt-1` (padding-top) between the section header and the expanded body to maintain visual rhythm.
- **Background tinting.** Per commit `1e7e027`, the section relies on specific background tints (`bg-red-50/40` and `dark:bg-red-950/20`) to maintain the "declined" visual-language; do not revert to neutral colors.
- **Empty sections should be collapsed.** Per commit `7e1371f`, ensure that if this component is used in a context where the list might be empty, the UX remains consistent with the "render empty sections collapsed" pattern.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.

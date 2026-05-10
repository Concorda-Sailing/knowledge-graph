---
node_id: concorda-web::src/components/dashboard/crew-card/invited-section.tsx::InvitedSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0fe83258de6453569a595364c06f538b8bba15dcd8655c559b9ea89f45c1288d
status: llm_drafted
---

# InvitedSection

## Purpose

Renders the list of pending crew invitations within a crew card. It provides UI controls for administrative actions: resending invitations (individually or in bulk), canceling an invitation, and marking an invitation as accepted or declined on behalf of the invitee. It is distinct from `AvailableSection` (which shows potential members) and `AcceptedSection` (which shows confirmed members).

## Invariants

- **`members` prop is an array of `SectionMember` objects.**
- **`onCancel` triggers a `DELETE event-crew` event.**
- **`onMarkAccepted` and `onMarkDeclined` are used to transition the state of an invitation via the API.**
- **The section is collapsed by default if `members.length === 0`** (via `useState(members.length === 0)`).
- **`busy` state management is local to the component.** The component tracks `busyResendId`, `busyMarkId`, and `busy` (for cancel) to prevent concurrent conflicting actions during async operations.

## Gotchas

- **Bulk actions vs. Individual actions:** Per commit `7e1371f`, the section is designed to handle both `onResendAll` and individual `onResend` calls. Ensure that `onResendAll` is properly implemented in the parent to handle the bulk state transition.
- **Visual spacing:** Per commit `a6d9494`, there is a specific requirement for `pt-1` (padding-top) between the section header and the expanded body to maintain visual consistency with the rest of the dashboard.
- **Background Tints:** Per commit `1e7e027`, the section uses a specific amber tint (`bg-amber-50/40 dark:bg-amber-950/20`) to distinguish the "Invited" state from "Available" or "Accepted" sections.

## Cross-cutting concerns

- **Auth**: Relies on the parent component's ability to execute authenticated API calls (e.g., `onCancel` or `onMarkAccepted`).
- **Side effects**: Successful execution of `onCancel` or `onMarkAccepted` will trigger a re-render of the `CrewMiniCard` and potentially update the total crew count/status in the dashboard view.

## External consumers

None known.

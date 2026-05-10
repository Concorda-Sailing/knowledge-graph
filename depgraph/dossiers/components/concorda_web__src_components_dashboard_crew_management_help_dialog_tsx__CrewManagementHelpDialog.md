---
node_id: concorda-web::src/components/dashboard/crew-management-help-dialog.tsx::CrewManagementHelpDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 527cfb2e4d906137fedfffd05b255b06f47987f73700c4985612c30b74676007
status: current
---

# CrewManagementHelpDialog

## Purpose

Provides a non-interactive, instructional overlay explaining the multi-step crew management workflow. It is a purely presentational component used to onboard users to the specific interaction patterns of the crew dashboard (e.g., priority ordering, toggle-based requests, and position assignment). Use this instead of creating new documentation components when explaining dashboard-specific UX patterns.

## Invariants

- **Purely presentational.** The component does not accept props or manage state; it is a static set of `Step` components.
- **Uses `Dialog` for accessibility.** The trigger is a ghost-variant `Button` with an `aria-label` and `title` to ensure screen readers identify the help intent.
- **Scrollable content.** The `DialogContent` is constrained by `max-h-[90vh]` and `overflow-y-auto` to prevent layout breakage on smaller viewports or mobile devices.

## Gotchas

- **Recent feature coupling.** Per commit `3b0268b`, this dialog was updated to include the "tap-to-assign positions" and "ordered invite picks" logic. If you are updating the crew management UI, you must also update these text descriptions to ensure the help dialog matches the actual implementation of the `CrewPositionsCard` and `AvailableSection`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: None. This is a static UI element.

## External consumers

None known.

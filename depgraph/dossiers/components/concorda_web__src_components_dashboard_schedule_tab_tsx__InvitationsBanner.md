---
node_id: concorda-web::src/components/dashboard/schedule-tab.tsx::InvitationsBanner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 32388c8e3a527030622a6fb720f844bc03bd47fb9fcccec78cdc1bc326e1644b
status: current
---

# InvitationsBanner

## Purpose

Renders a notification banner for pending crew invitations on the Schedule tab. It displays a list of upcoming events where the user has been invited, showing the event name, date, and the person who sent the invitation. It provides interactive controls for selecting a position (via a dropdown) and responding to the invitation (Accept/Decline).

## Invariants

- **`tz` is required for date rendering.** The component uses `formatInOrgTz` to ensure the event date is displayed in the organization's local time, not the user's browser time.
- **`invitations` must be non-empty to render.** If the array length is 0, the component returns `null` and occupies no space in the DOM.
- **`respondingId` tracks active state.** The `isBusy` state is driven by comparing the invitation ID to `respondingId`, which disables the buttons during an async operation to prevent double-submissions.
- **`selectedPositions` is a keyed record.** The `Select` component uses `inv.id` as the key to track which position is currently selected for a specific invitation.

## Gotchas

- **Timezone rendering fix:** Per commit `f444b4c`, all backend datetimes must be rendered using `formatInOrgTz` with the provided `tz` prop. Failing to do this results in the user seeing the event time in their local browser timezone rather than the organization's timezone.
- **Mobile responsiveness:** Per commit `21f7cb5`, the banner uses `max-md:w-full` on the action container to ensure the Accept/Decline buttons stack or expand correctly on small screens.
- **Empty state visibility:** The component relies on `inv.event_name || "Sailing Event"` to provide a fallback string if the event name is missing, preventing empty-looking UI rows.

## Cross-cutting concerns

- **Auth**: None (relies on parent component to provide the `onRespond` and `onSelectPosition` handlers which are bound to authenticated API calls).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Triggers state updates in the `ScheduleTab` via `onSelectPosition` and `onRespond`.

## External consumers

None known.

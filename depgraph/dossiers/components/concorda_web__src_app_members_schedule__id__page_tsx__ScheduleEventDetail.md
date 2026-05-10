---
node_id: concorda-web::src/app/members/schedule/[id]/page.tsx::ScheduleEventDetail
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bef5f6b19283c52139f707fbb0b69bb7cbb84229830b63b8f7bba5f8e5d65639
status: llm_drafted
---

# ScheduleEventDetail

## Purpose

The primary detail view for a specific scheduled event. It serves as the landing page for users arriving via email links (e.g., "Accept or decline" invites) and provides a centralized interface for managing event logistics, crew assignments, and regatta-specific details. It manages complex local state for multiple modes: viewing event info, editing logistics (departure/arrival), and managing crew/position slots.

## Invariants

- **`eventId` is the primary key** used to fetch the specific event detail from the API.
- **`onBack` must be provided** to ensure the user can return to the main schedule tab (typically `/members?tab=schedule`).
- **Time rendering must use `formatInOrgTz`** to ensure departure/arrival times reflect the organization's local time rather than the viewer's browser time.
- **`toTime` helper handles empty strings** by returning an empty string, preventing "Invalid Date" or NaN errors in the UI.

## Gotchas

- **Decoupling from `mySchedule`**: Per commit `1b5d864`, this component must call `/api/events/{id}/detail` directly rather than relying on a passed-in `mySchedule` object to avoid stale data or coupling.
- **Timezone consistency**: Per commit `f444b4c`, all backend datetimes must be rendered using the organization's timezone via `formatInOrgTz` to prevent the "traveling sailor" bug where local browser time displays the wrong event time.
- **State-heavy UI transitions**: The component manages many distinct boolean states (e.g., `editingLogistics`, `confirmRemove`, `confirmSaveLogistics`). Changes to the form or data fetching logic must carefully manage these to avoid "stuck" loading states or broken confirmation dialogs.
- **Crew Invite UX**: The component tracks `respondingAction` to handle the specific flow where a user accepts or declines an invite directly from an email link, ensuring buttons are disabled during the in-flight request.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to determine user identity; visibility of certain actions (like editing or removing) is gated by user permissions.
- **Audit**: Changes to event logistics or crew assignments (via the `form` state) trigger API calls that result in audit logs on the backend.
- **Side effects**: Updates to the event detail or crew assignments will trigger re-renders/re-fetches in the parent schedule view if the user navigates back.

## External consumers

None known.

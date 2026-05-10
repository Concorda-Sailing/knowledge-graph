---
node_id: concorda-web::src/app/members/schedule/[id]/page.tsx::ScheduleDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e60b378ec527cf59bcc3b3758b95266c1e04541fb6191f1b7771623dc4c99b17
status: current
---

# ScheduleDetailPage

## Purpose

The `ScheduleDetailPage` provides a deep-dive view for a specific event, handling both the display of event details (logistics, crew, and regatta info) and the interactive management of that event. It serves as the landing page for users arriving via email links (e.g., "Accept or decline" invites). The component is split into a routing wrapper that handles the `params`-based `id` and the core `ScheduleEventDetail` which manages the complex state of the event.

## Invariants

- **`onBack` must be a manual redirect.** Because users often arrive via email links with no browser history, the `onBack` prop is hardcoded to `router.push("/members?tab=schedule")` to ensure the user isn't stuck in a dead-end.
- **`eventId` is a required string.** The component relies on the URL parameter to fetch the specific event data.
- **State is highly fragmented.** The component manages numerous independent pieces of state (loading, editing, saving, removing, and responding) to allow for granular UI feedback during asynchronous operations.

## Gotchas

- **Email link history trap:** If a user opens the page from an email, `router.back()` is a no-op. The `ScheduleDetailPage` wrapper must use `router.push` to a known safe route (the schedule tab) to prevent broken navigation flows (see commit `3d680f4`).
- **Decoupling from `mySchedule`:** The detail page must call `/api/events/{id}/detail` directly rather than relying on local `mySchedule` state to ensure it shows the most recent, authoritative data for the specific event (see commit `1b5d864`).
- **Timezone rendering:** All backend datetimes must be rendered using the organization's timezone, not the browser's local time, to avoid confusion during event-start-time displays (see commit `f444b4c`).
- **Crew/Config synchronization:** The UI must re-sync crew position slots to the live configuration on load to prevent stale or orphaned assignments (see commit `8baf60f`).

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to determine user identity and `useBoats` for boat-related context.
- **Side effects**: Updates to the event (e.g., changing departure time or crew) affect the visibility of the "looking for a ride" badge and the overall event status.

## External consumers

None known.

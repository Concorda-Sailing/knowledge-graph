---
node_id: concorda-web::src/app/events/[slug]/checkin/page.tsx::CheckinPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8543bd46d780027f50aa5f0094867249f423955a6b5cf2af32865ccb4297597f
status: llm_drafted
---

# CheckinPage

## Purpose

The `CheckinPage` is a specialized view for event staff to check in attendees via a registration ID. It handles the lifecycle of a check-in attempt, transitioning from a loading state to a "ready" state once the event slug and `reg` search parameter are validated. It is distinct from the general event detail page as it is an action-oriented interface that mutates attendee status via `eventsApi.checkin`.

## Invariants

- **Requires `reg` search parameter.** The page will transition to an error state if the `reg` parameter is missing from the URL.
- **`eventsApi.getBySlug(slug)` is the primary data fetch.** The page must successfully fetch the event metadata before allowing a check-in attempt.
- **State transitions are strictly linear.** The component moves from `loading` -> `ready` -> `checking` -> `success` or `error`.
- **Error handling is semantic.** The component parses error messages to provide specific feedback for "already checked in" or "permission" issues.

## Gotchas

- **Timezone rendering.** Per commit `f444b4c`, any datetime data returned in the `result` object (specifically `checked_in_at`) must be rendered using the organization's timezone, not the browser's local time, to ensure consistency for staff.
- **Error message parsing.** The `handleCheckin` function relies on string matching (e.g., `message.includes("already checked in")`) to differentiate between a user error and a permission error. If the API error strings change, the UI feedback will become generic.

## Cross-cutting concerns

- **Auth**: Uses `eventsApi.checkin` which requires valid session/permission context.
- **Side effects**: Successful check-in updates the attendee's status in the backend, which may trigger downstream notifications or dashboard updates.

## External consumers

None known.

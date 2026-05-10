---
node_id: concorda-web::src/components/dashboard/crew-requests-card.tsx::CrewRequestsCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1fe81327e62b132876f7c81aa89d852ffcb814a0afe4a80ed0db69a1880e4372
status: llm_drafted
---

# CrewRequestsCard

## Purpose

Displays a list of pending crew requests for an event, allowing an organizer to accept or decline them. It is a specialized view for the dashboard that handles the local UI state of a response (loading/busy state) to prevent multiple clicks. Use this when you need a high-level, interactive list of `EventCrewMember` objects that requires immediate action, rather than a read-only list.

## Invariants

- **`requests` must be an array of `EventCrewMember`**.
- **`onRespond` is the primary driver of state change.** It must handle the asynchronous logic of updating the backend.
- **`respondingId` tracks the active operation.** Only one button (Accept or Decline) is disabled at a time per member to prevent race conditions during the `onRespond` call.
- **Returns `null` if the list is empty.** The component does not render a card container if there are no pending requests.

## Gotchas

- **In-flight protection is mandatory.** Per commit `3595c37`, the component uses `respondingId` and a `try...finally` block in the `handle` function to ensure buttons are disabled while `onRespond` is executing. This prevents users from double-clicking or triggering multiple API calls for the same request.
- **Aria-labels are required for accessibility.** Per commit `3595c37`, buttons must include `aria-label={`Accept ${fullName}`}` and `aria-label={`Decline ${fullName}`}` to ensure screen readers can distinguish between the two actions in the list.
- **Initials fallback logic.** The component manually constructs initials from `person_first_name` and `person_last_name`. If these fields are missing or null, the component relies on the `AvatarFallback` to prevent a crash.

## Cross-cutting concerns

- **Auth**: Depends on the parent component's ability to call `onRespond` (typically requires an authenticated organizer role).
- **Side effects**: Successful responses via `onRespond` will trigger a re-render of the dashboard, reducing the `requests.length` count in the `Badge`.

## External consumers

None known.

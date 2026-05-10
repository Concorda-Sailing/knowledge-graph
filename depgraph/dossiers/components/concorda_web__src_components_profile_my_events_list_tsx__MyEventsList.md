---
node_id: concorda-web::src/components/profile/my-events-list.tsx::MyEventsList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf793d7dfaebfeb6090c40e75afabd2883b650dda97e954a0bb7127eb48a2914
status: llm_drafted
---

# MyEventsList

## Purpose

Displays a list of an authenticated user's event registrations within their profile section. It fetches data via `profileApi.getEventRegistrations`, renders each registration using the `EventCard` component, and allows users to cancel active registrations. Use this component when you need to show a user's personal event schedule rather than a general event directory.

## Invariants

- **Fetches via `profileApi.getEventRegistrations()`** — the component relies on this specific endpoint to populate the list.
- **`isPast` logic is derived from `reg.event_date`** — uses `parseISO` and `isFuture` from `date-fns` to determine if the "Cancel" action should be enabled.
- **Stateful cancellation** — calling `handleCancel` performs an optimistic-style update by filtering the local `registrations` state after the API call succeeds.

## Gotchas

- **`onCancelRegistration` is disabled for past events** — per the implementation of `EventCard` (line 63), the cancel button is only functional if `isPast` is false. This prevents users from attempting to cancel events that have already occurred.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to call `profileApi.getEventRegistrations`.
- **Side effects**: Successful cancellation via `handleCancel` triggers a state update in this component to remove the item from the UI immediately.

## External consumers

None known.

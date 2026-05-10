---
node_id: concorda-web::src/components/event-card.tsx::EventCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9ee5f96e5fee5eb094d9db66fcd3c626d2516fbc77cdd7e5945ea473582b44e3
status: current
---

# EventCard

## Purpose

The `EventCard` component provides a visual summary of an event, used to display either a full `Event` object or a `MyEventRegistration` (for a user's specific participation). It serves as the primary UI element for event snapshots in lists and detail views. Use this when you need a standardized, styled representation of an event that handles both the full event data and the user's registration status (e.g., "Confirmed" or "Past").

## Invariants

- **Data Fallback Logic**: The component derives display values (name, date, location, slug) by checking the `event` object first, then falling back to the `registration` object.
- **Timezone Consistency**: All date rendering must use `formatInOrgTz` with the `timezone` from `useConstants()` to ensure the event time matches the organization's local time rather than the user's browser time.
- **Cancellation Flow**: If `onCancelRegistration` is provided, the component manages a local `cancelling` state to prevent multiple simultaneous clicks during the async operation.
- **Visual State**: The background color of the icon container shifts from `bg-primary/10` to `bg-muted` based on the `isPast` prop.

## Gotchas

- **Timezone Rendering**: Per commit `f444b4c`, all backend datetimes must be rendered using the organization's timezone. Using a standard `toLocaleString()` or failing to pass the `timezone` to `formatInOrgTz` will result in incorrect local time display for the user.
- **Registration Dependency**: The `handleCancel` function relies on `registration.id`. If `onCancelRegistration` is called without a valid registration object, the function returns early without error, but the UI may appear stuck if the parent doesn't handle the empty state.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The `onCancelRegistration` callback typically triggers a state update in the parent list (e.g., `MyEventsList`), which may involve a subsequent API call to update the registration status.

## External consumers

None known.

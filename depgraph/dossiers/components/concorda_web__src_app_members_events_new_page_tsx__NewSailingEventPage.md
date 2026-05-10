---
node_id: concorda-web::src/app/members/events/new/page.tsx::NewSailingEventPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 811b925f174c890323b4d5846be4aef2207fddce1297bc26b24fc485f903e47d
status: llm_drafted
---

# NewSailingEventPage

## Purpose

The `NewSailingEventPage` is a dedicated route for creating new sailing events (e.g., races, training, or cruises). It provides a structured form to capture event details, including a boat selection (fetched via `profileApi.getBoats()`) and time-specific data. It is distinct from the previous dialog-based implementation, now serving as a standalone page to allow for a more robust, dedicated UI for complex event creation.

## Invariants

- **Mandatory fields**: The `handleSave` function requires `date`, `dockTime`, and `duration` to be present; otherwise, the submission is silently aborted.
- **Timezone conversion**: The component uses `orgInputToUtcIso` to convert local date/time strings into UTC ISO strings before sending them to the API.
- **Boat selection**: If the user has exactly one boat, the `boatUuid` is automatically selected via `setBoatUuid(bs[0].id)` to reduce friction.
- **Navigation**: Upon successful creation, the user is redirected to the specific event's detail page via `/members/schedule/${result.event.id}`.

## Gotchas

- **Naive time preservation**: Per commit `3263c65`, the form must preserve the user's intended local time during the conversion to UTC to avoid the "naive local time" drift issue common in event creation.
- **Strict dependency on `orgInputToUtcIso`**: Because the form relies on `date` and `dockTime` strings to build the ISO string, any failure in the `timezone` provided by `useConstants()` will result in incorrect event scheduling.
- **Form-to-API mapping**: The `duration` field is passed as `estimated_duration` to the `eventsApi.createCustom` method.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` and `eventsApi` which require an authenticated session.
- **Side effects**: Successful creation triggers a redirect to the member's schedule view.

## External consumers

None known.

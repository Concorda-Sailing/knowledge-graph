---
node_id: concorda-web::src/lib/api.ts::eventsApi.getSailingEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65b9988564bd0acf4f339cf22b9c2ec1ebd9fee8b34993e4932961af2dc214ee
status: llm_drafted
---

# eventsApi.getSailingEvent

## Purpose

Fetches the specialized `SailingEvent` metadata associated with a specific event ID. This is distinct from the standard `Event` object, as it contains the specific nautical/logistical details (like dock times or crew configurations) required for the sailing-specific views. Use this when you need the "sailing" layer of an event rather than the general event metadata.

## Invariants

- **Returns a `SailingEvent` object.** This is a specialized type that extends the base event concept with nautical parameters.
- **Uses `fetchApiAuthenticated`.** Requires a valid bearer token to access the `/api/events/${eventId}/sailing-event` endpoint.
- **GET request only.** This specific method is a read-only operation; use `upsertSailingEvent` for modifications.

## Gotchas

- **Coupling with `mySchedule`.** Per commit `1b5d864`, the detail page was previously calling `/api/events/{id}/detail` and was over-coupled to `mySchedule` logic; ensure you are calling this specific endpoint to avoid pulling unnecessary schedule-specific state when only the sailing metadata is needed.
- **Data shape dependency.** Recent changes in the crew/schedule logic (e.g., `bf44b09`) suggest that the structure of the returned object is sensitive to how `EventCrewStatus` and schedule-card pool handling are implemented.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` (bearer token).
- **Side effects**: Changes to the data returned by this method (via `upsertSailingEvent`) will impact the "looking for a ride" detail view and the "accepting-crew" status/count displayed on schedule cards (per commit `2d6b8a7`).

## External consumers

None known.

---
node_id: concorda-web::src/lib/api.ts::eventsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 22e94c574e03ba62154e59413cb7a5fec373d344939926aa69feb137d639c467
status: llm_drafted
---

# eventsApi.update

## Purpose

Updates the core metadata of a specific event. It is used to modify properties of an existing `Event` via a `PUT` request to the `/api/events/${id}` endpoint. This is distinct from `upsertSailingEvent`, which specifically targets the nested `SailingEvent` data structure.

## Invariants

- **Method is `PUT`** — requires a full `EventUpdate` object to satisfy the API contract.
- **Requires authentication** — uses `fetchApiAuthenticated` to ensure the caller has the necessary permissions to modify event data.
- **Returns the updated `Event` object** — the response shape matches the `Event` type.

## Gotchas

- **Avoid coupling with `mySchedule`** — per commit `b4d60c6`, the detail page was previously calling `/api/events/{id}/detail` which created an unnecessary coupling with the user's personal schedule; ensure updates target the base event ID to avoid this.
- **Schema mismatch on boat configuration** — per commit `bf15808`, ensure you are not attempting to match shapes manually; use the provided `EventUpdate` type to ensure the `boat_config_id` and other properties are passed correctly.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to verify user permissions for the specific event.
- **Side effects**: Updates to this endpoint will propagate to the `ScheduleEventDetail` page and any UI components displaying the event's primary metadata.

## External consumers

None known.

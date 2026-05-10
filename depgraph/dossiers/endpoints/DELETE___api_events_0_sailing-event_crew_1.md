---
node_id: DELETE::/api/events/{0}/sailing-event/crew/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: acbda45749116723887b17a30ff29e7f5218965ab325c52ac2b11362dae004f2
status: llm_drafted
---

# DELETE /api/events/{event_id}/sailing-event/crew/{person_uuid}

## Purpose

Removes a specific person from a sailing event's crew roster. It is used to decouple a user from an event, whether they were an invited participant or a confirmed crew member. This is distinct from the `crew-pool` endpoints which manage the broader pool of potential participants; this endpoint targets a specific `person_uuid` for immediate removal.

## Invariants

- **HTTP Method/Path**: `DELETE /api/events/{event_id}/sailing-event/crew/{person_uuid}`.
- **Auth**: Requires `require_auth` and a successful call to `_get_user_sailing_event_or_404` with the `relation="owner"` check.
- **Return Shape**: Returns a `204 No Content` on success.
- **Error State**: Raises a `404` if the `person_uuid` does not exist within the context of the specified `event_id`.

## Gotchas

- **Calendar side-effects**: If the crew member's status is `invited`, `accepted`, or `confirmed`, the system attempts to send a cancellation email via `_send_calendar_email_for_crew` before deleting the row. This is a critical step to ensure the user's external calendar is updated.
- **Order of operations**: The cancellation email must be triggered *before* `db.delete(ec)` to ensure the record is still accessible to the email renderer.
- **Silent failure on email**: The email dispatch is wrapped in a `try/except` block (per `_send_calendar_email_for_crew`) to prevent a failed email from blocking the database deletion.

## Cross-cutting concerns

- **Auth**: Restricted to the event owner via `_get_user_sailing_event_or_404(..., relation="owner")`.
- **Websocket**: Emits `EVENT_CREW_UPDATED` for the specific `event_id` after successful deletion.
- **Side effects**: Triggers calendar/email-based removal logic if the user had an active status.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.removeEventCrew`

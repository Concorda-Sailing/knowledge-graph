---
node_id: POST::/api/events/{0}/sailing-event/crew-confirm
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 51a9cb40b54a43016d81ee2089dccf64c550f4ea1eb5061692cfa27641269c76
status: llm_drafted
---

# POST /api/events/{event_id}/sailing-event/crew-confirm

## Purpose

Finalizes the crew for a sailing event by transitioning all "accepted" members to "confirmed" status. This endpoint is a decisive state change that must complete even if downstream notifications fail. It is distinct from the crew-pool endpoint, which manages the pool of potential members; this endpoint is the final step in the lifecycle of an event's crew.

## Invariants

- **Requires `owner` relationship** — The `current_user` must be the owner of the sailing event via `_get_user_sailing_event_or_404`.
- **Two-phase execution** — The database commit for `se.crew_confirmed = True` and `ec.status = EventCrewStatus.CONFIRMED` must occur before any notification logic is executed.
- **Notification failure is non-blocking** — Per the docstring, a failure in `_notify` or `render_event_crew_confirmed_email` must not roll back the database transaction.
- **Returns `SailingEventRead`** — The response shape is governed by the `SailingEventRead` model.

## Gotchas

- **Notification/Email failures are swallowed** — The `except Exception as e: # noqa: BLE001` block ensures that a failed email does not roll back the crew confirmation. This is a deliberate design choice to ensure the state transition is the source of truth.
- **Timezone-aware dock times** — Per commit `6c314f5`, the `dock_time` rendered in the email must be localized to the organization's timezone (via `_to_org_local`) rather than being sent as a raw UTC string, to prevent confusion for the crew.
- **Strict ordering of side effects** — The `db.commit()` must happen before `broadcast_event` and the notification loop to ensure the state is durable before external systems (like the frontend or email workers) react to the change.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and specifically validates the user as the event `owner`.
- **Websocket**: Emits `EVENT_CREW_UPDATED` via `broadcast_event` once the state is committed.
- **Audit**: N/A.
- **Side effects**: Triggers the "crew confirmed" email notification to all members with an "accepted" status.

## External consumers

- `concorda-web`: `eventsApi.confirmEventCrew` is used to finalize the crew list in the UI.

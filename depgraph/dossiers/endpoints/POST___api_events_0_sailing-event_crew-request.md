---
node_id: POST::/api/events/{0}/sailing-event/crew-request
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e9399c0c11037a0f082de925a33689eaf6b8586045bfac7cbb4129ae70afbb1f
status: llm_drafted
---

# POST /api/events/{event_id}/sailing-event/crew-request

## Purpose

Allows a user to request to join a specific boat for a given sailing event. The endpoint requires a `boat_uuid` to disambiguate between multiple boats that might be associated with a single event (multi-captain scenario). It creates an `EventCrew` record with a `status` of `"requested"` and a `self_selected` flag set to `true`.

## Invariants

- **Requires `boat_uuid`** — The request must explicitly target a boat to prevent routing the request to the wrong vessel in multi-boat events.
- **`current_user` is required** — Uses `require_auth` to identify the requester.
- **Returns `EventCrewRead`** — The response shape is the serialized `EventCrew` record.
- **Status is fixed at `"requested"`** — This endpoint only initiates the request; it does not handle acceptance or rejection.

## Gotchas

- **Ownership restriction** — A user cannot request to join a boat they already own. The check `if owner:` (lines 2997-3003) raises a 400 error if the `current_user` is the owner of the target `boat_uuid`.
- **Acceptance check** — The request will fail with a 403 if the `SailingEvent` has `accept_crew_requests` set to `False`.
- **Duplicate prevention** — If a record already exists for the `(event_id, person_uuid)` pair, the API returns a 409 error (line 3011).
- **Notification dependency** — The endpoint triggers an email via `render_event_crew_request_to_owner_email`. Per commit `8f84d2d`, this requires specific hardening of the renderer to ensure the `event_crew_id` and `notes` are passed correctly to avoid broken links in the owner's email.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user).
- **Websocket**: Emits `EVENT_CREW_UPDATED` for the specific `se.id` (line 3023).
- **Audit**: N/A.
- **Side effects**: Triggers an email notification to the `boat_owner` via `_notify` (line 3048).

## External consumers

- `concorda-web` (via `eventsApi.requestToCrew`)
- `concorda-test` (via `ApiClient.requestToCrew`)

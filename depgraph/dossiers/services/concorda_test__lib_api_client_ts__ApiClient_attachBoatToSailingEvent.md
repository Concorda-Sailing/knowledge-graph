---
node_id: concorda-test::lib/api-client.ts::ApiClient.attachBoatToSailingEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e5a0d355863c717d76f011e9854095908b2059510c3366dfdbf6a4df21577102
status: llm_drafted
---

# ApiClient.attachBoatToSailingEvent

## Purpose

Links a specific boat to a sailing event via a `PUT` request. This is a specialized helper used to transition an event from a generic state to a specific sailing event with a designated boat. It is distinct from `upsertSailingEvent`, which is used for updating logistical details (like dock times or departure locations) once the boat is already attached.

## Invariants

- **HTTP Method is `PUT`** — Uses `this.put` to target the `/api/events/${eventId}/sailing-event` endpoint.
- **Payload structure** — Expects a single object containing `boat_uuid`.
- **Endpoint path** — Requires a valid `eventId` to construct the specific resource path.

## Gotchas

- **Email-link flow dependency** — Per commit `0990b5d`, this method is a critical part of the "boat-crew and crew-request email-link flows." Tests involving email-based acceptance/declining must ensure the boat is correctly attached to the event first, or the subsequent crew-request logic will fail to resolve correctly.
- **Auth/Policy requirements** — Per commit `c70d472`, ensure the global setup is correctly handling pending policies; if the user context lacks the necessary permissions to modify event-specific logistics, this call will fail.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (via `ApiClient` instance).
- **Side effects**: Successful attachment is a prerequisite for the "crew_request_to_owner" email flow and the visibility of the boat in the "Boats tab" (per commit `c8b6d75`).

## External consumers

None known.

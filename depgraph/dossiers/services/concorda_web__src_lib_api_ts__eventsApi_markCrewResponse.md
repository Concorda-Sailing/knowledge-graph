---
node_id: concorda-web::src/lib/api.ts::eventsApi.markCrewResponse
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 22f81065b914e4437c16e27190f4b557451d5b04f2da3e59ea2389321626b8d3
status: current
---

# eventsApi.markCrewResponse

## Purpose

The `markCrewResponse` method handles the user's decision to accept or decline a crew invitation for a specific sailing event. It is a specialized subset of the crew management lifecycle, distinct from `assignCrew` (which is an administrative action) and `respondToCrewRequest` (which is used for boat-to-event requests). Use this when a user is explicitly responding to an invitation to join a specific event's crew.

## Invariants

- **HTTP Method is `PUT`** — follows the pattern for updating existing resource states.
- **Requires `eventId` and `personUuid`** — both are necessary to identify the specific invitation being acted upon.
- **Input `action` is a strict union** — must be exactly `"accept"` or `"decline"`.
- **Returns `EventCrewMember`** — the response provides the updated state of the crew member record.
- **Uses `fetchApiAuthenticated`** — requires a valid session/token to execute.

## Gotchas

- **Decoupling from position-name** — per commit `b4d60c6`, the logic for counting accepted invites vs. live slot counts was decoupled from `position-name` gating. Ensure that marking a response does not inadvertently rely on or require a `position_name` to be present, as the API handles the status transition via the `action` alone.
- **Relationship to `SailingEvent` state** — per commit `2d69bfa`, marking a response is a key driver for the "accepting-crew" status badge on regatta detail views.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Directly impacts the visibility of the "accepting-crew" status on the regatta detail page and the schedule card count.

## External consumers

- `EventCrewCard` in `event-crew-card.tsx` (via `hook_call`).

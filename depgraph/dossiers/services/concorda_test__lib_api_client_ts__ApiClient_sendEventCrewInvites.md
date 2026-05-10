---
node_id: concorda-test::lib/api-client.ts::ApiClient.sendEventCrewInvites
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0596346f7a2b088b4cf201afc68c097a030fe69befd2b0e98e583f8a1e486b2f
status: current
---

# ApiClient.sendEventCrewInvites

## Purpose

Triggers the invitation process for crew members to a specific sailing event. It posts to the `/api/events/{eventId}/sailing-event/crew-invite` endpoint, allowing a user to invite a list of people via their UUIDs. This is distinct from `setEventCrewPool`, which manages the persistent pool of potential crew, whereas this method specifically initiates the invitation/notification flow.

## Invariants

- **HTTP Method is `POST`** — used to trigger the side-effect of sending invitations.
- **Input `person_uuids` is nullable** — if `personUuids` is not provided, it defaults to `null` in the request body.
- **Returns `Promise<unknown>`** — the exact response shape is not typed here, but it follows the standard API response pattern.

## Gotchas

- **Requires authenticated context** — like other `ApiClient` methods, this relies on a valid bearer token being present in the instance.
- **Recent coverage expansion** — per commit `0990b5d`, this method is part of the new flow to cover email-link paths for both boat-crew and crew-request scenarios.

## Cross-cutting concerns

- **Auth**: Requires a valid session/token via the `ApiClient` instance.
- **Side effects**: Triggers the email-link flows (accept/decline) that are tracked in `cross-context-crew.spec.ts`.

## External consumers

- `concorda-test::tests/dashboard/cross-context-crew.spec.ts` (used in both test hooks).

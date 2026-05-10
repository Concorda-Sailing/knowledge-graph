---
node_id: concorda-test::lib/api-client.ts::ApiClient.respondToEventCrewInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c512e63b54d42858ebae3eee2550da64372a2e776ff50428f235d57aa8c10c1f
status: current
---

# ApiClient.respondToEventCrewInvite

## Purpose

The helper for a user to accept or decline a crew invitation for a specific event. It performs a `PUT` request to the `/sailing-event/crew-respond` endpoint. Use this instead of `sendEventCrewInvites` when simulating the response of an invited person, and ensure `positionName` is provided if the role requires a specific designation.

## Invariants

- **HTTP Method is `PUT`** — uses a state-changing verb to finalize the invitation response.
- **Requires `eventId` and `action`** — the `action` must be exactly `"accept"` or `"decline"`.
- **Payload structure** — sends `{ action, position_name: string | undefined }`.
- **Returns `Promise<unknown>`** — the response body is not explicitly typed in the client, but the API expects the action/position shape.

## Gotchas

- **Recent alignment with UI** — commit `705f5bd` indicates the API and this client were recently adjusted to align with the current UI behavior on the test host.
- **Dependency on `eventId`** — if the event ID is invalid or the user is not actually invited, the API response will likely fail, which is a common failure point in `cross-context-crew.spec.ts`.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token on the `ApiClient` instance (established via `login`).
- **Side effects**: Successful calls update the crew list for the event, which is visible in the `getEventCrew` output and affects the "crew" status of the person in the event context.

## External consumers

- Internal to `concorda-test`. Used by `cross-context-crew.spec.ts` to simulate user-side acceptance/declination of invites.

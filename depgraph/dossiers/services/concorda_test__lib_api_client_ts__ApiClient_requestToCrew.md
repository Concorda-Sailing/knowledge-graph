---
node_id: concorda-test::lib/api-client.ts::ApiClient.requestToCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 467d4b423c83fb26a37075eadb6fe3d25872911b53e50f4b179b9771fdddf052
status: llm_drafted
---

# ApiClient.requestToCrew

## Purpose

The `requestToCrew` method initiates a sailor-driven request to join a specific boat at an event. It is used to simulate the flow where a user expresses interest in a boat, which subsequently triggers an email notification to the boat owner containing direct action links. This is a distinct step from `sendEventCrewInvites`, which is the administrative/owner-driven action of inviting specific users.

## Invariants

- **HTTP Method is `POST`** — targets the `/api/events/${eventId}/sailing-event/crew-request` endpoint.
- **Requires `eventId` and `boatUuid`** — both are mandatory string arguments.
- **Returns a Promise resolving to `{ id: string; status: string }`** — the response shape is fixed for the UI to track the request state.
- **`notes` is optional** — can be passed as a string to provide context for the request.

## Gotchas

- **Email triggers via `/api/invite/respond`** — as noted in the source doc, the resulting `crew_request_to_owner` email contains links that resolve through the `respond` endpoint. Tests must ensure the full lifecycle (request -> email -> respond) is covered.
- **Recent coverage requirement** — per commit `0990b5d`, this method is critical for covering the "boat-crew and crew-request email-link flows" and requires trace/screenshot artifacts for verification.
- **Dependency on event/boat existence** — if the `boatUuid` is not associated with the `eventId` in the test seed, the request will fail (implied by the endpoint structure).

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token on the `ApiClient` instance.
- **Side effects**: Triggers the `crew_request_to_owner` email flow.

## External consumers

- `concorda-test::tests/auth/email-link-flows.spec.ts` (specifically via `test@373`).

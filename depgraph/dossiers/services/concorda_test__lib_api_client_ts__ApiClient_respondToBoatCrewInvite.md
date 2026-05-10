---
node_id: concorda-test::lib/api-client.ts::ApiClient.respondToBoatCrewInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 21a3a2c6c8d011d06f5ccb5fa5dab2bd4059d7cfbb189914b5504326f20aba0f
status: llm_drafted
---

# ApiClient.respondToBoatCrewInvite

## Purpose

The method handles the resolution of a crew invitation for a specific boat. It sends a `PUT` request to the `/api/boats/${boatId}/crew-invite/respond` endpoint with the user's decision (`accept` or `decline`). This is a critical step in the email-link flow where a user interacts with an invitation sent via email.

## Invariants

- **Method is `PUT`** — Uses a PUT request to signal a state change in the invitation status.
- **Requires `boatId` and `action`** — The `action` must be exactly `"accept"` or `"declined"` to satisfy the union type.
- **Returns `Promise<unknown>`** — The return value is not parsed by this method, as the primary goal is the side effect of updating the crew status.

## Gotchas

- **Email link flow dependency** — As noted in commit `379ec4b`, this method is central to testing the "emailed accept/decline links" for co-owner and race-crew invites. If the logic for parsing the action from the URL changes, this method's call site in the spec will fail.
- **Auth/Policy requirements** — Per commit `c70d472`, ensure that the test setup handles pending policies correctly; if the user's identity or permissions are not correctly established via the `ApiClient` before calling this, the response may fail due to policy violations.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token established via `ApiClient.login`.
- **Side effects**: Successfully calling this method triggers the state change that allows a user to appear in the boat's crew list, which is verified in the `Boats` tab in `cross-context-crew.spec.ts`.

## External consumers

- `concorda-test::tests/dashboard/cross-context-crew.spec.ts` (specifically test@8)

---
node_id: concorda-test::lib/api-client.ts::ApiClient.requestCoowner
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae33afb12db26273c048ba70fca28cd29899bafcfa6dfc3b5f3e95bde07178b6
status: current
---

# ApiClient.requestCoowner

## Purpose

The `requestCoowner` method initiates a request to add a co-owner to a specific boat. It is used in E2E tests to simulate the workflow where a boat owner invites another user to join the boat's management or crew. This is a distinct step from `coownerInvite`, which is the subsequent action of sending the actual invitation to a user.

## Invariants

- **POST to `/api/boats/${boatId}/coowner-request`** — the method must use the POST verb to trigger the state change.
- **Returns a `request_id` and `boat_crew_uuid`** — the response shape is a fixed object used to track the pending request.
- **Requires a valid `boatId`** — the operation is scoped to a specific boat resource.

## Gotchas

- **Avoid `/auth/accept-tos` for policy bypass** — per commit `c70d472`, the global setup was previously attempting to use a bogus `/auth/accept-tos` endpoint to clear pending policies. Instead, use `acceptAllPendingPolicies()` to ensure the user is not gated by a Terms of Service prompt during navigation.
- **Sequence matters for E2E flows** — as seen in `379ec4b`, this method is part of a multi-step flow (request -> invite -> respond). If the `request_id` is not captured or the sequence is broken, the subsequent `coownerInvite` or `respondToInvite` calls will fail to find the active request context.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token established via `ApiClient.login`.
- **Side effects**: Successful execution triggers the creation of a pending approval/invite state that must be handled by the recipient to complete the boat-crew association.

## External consumers

None known.

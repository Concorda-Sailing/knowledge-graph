---
node_id: concorda-test::lib/api-client.ts::ApiClient.coownerInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fbc50b047e1d9b0adee11875bee506de5a59d5ea488493d8f536288601bbef3e
status: llm_drafted
---

# ApiClient.coownerInvite

## Purpose

Sends a POST request to `/api/boats/${boatId}/coowner-invite` to initiate a co-owner invitation. This method is used to test the lifecycle of boat ownership transfers and crew-related access flows. It is distinct from `requestCoowner`, which is used for the initial request phase; `coownerInvite` is the specific action that triggers the invitation to a person or email.

## Invariants

- **HTTP Method is `POST`** — uses the `this.post` helper to ensure the body is serialized.
- **Requires `boatId`** — the endpoint is scoped to a specific boat resource.
- **Body structure** — accepts an optional `person_uuid` or `email` to identify the invite recipient.
- **Returns `request_id`** — the response contains a single string `request_id` used to track the invitation status.

## Gotchas

- **Policy Gating** — per commit `c70d472`, ensure that tests calling this (or subsequent flows) do not get blocked by unaccepted Terms of Service. While this method doesn't handle policies, the user identity used to call it must have already executed `acceptAllPendingPolicies()` to avoid navigation/access-gate failures in the UI.

## Cross-cutting concerns

- **Auth**: Requires a bearer token from a logged-in `ApiClient` instance.
- **Side effects**: Triggers the creation of an invitation record which is visible in the co-owner inbox/notification flows.

## External consumers

- `concorda-test::tests/boats/coowner-inbox.spec.ts` (used in tests for both successful and negative path flows).

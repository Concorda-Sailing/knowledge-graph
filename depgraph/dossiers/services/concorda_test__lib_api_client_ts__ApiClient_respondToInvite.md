---
node_id: concorda-test::lib/api-client.ts::ApiClient.respondToInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1bfd1fe8d8e307ea3f220f7fec6b9a8a6cf59c2e315f17e95ef5f67264a06430
status: llm_drafted
---

# ApiClient.respondToInvite

## Purpose

The method used to finalize a user's response to a pending invitation (e.g., co-owner or crew invites). It submits a decision of either `'accepted'` or `'declined'` for a specific invitation ID. This is a critical step in testing end-to-end flows where a user must interact with an email-driven link to join a boat or a crew.

## Invariants

- **HTTP Method is `POST`** — sends the decision to `/api/invite/respond`.
- **Input `id` is the invitation UUID.**
- **Input `decision` is strictly `'accepted' | 'declined'`**.
- **Returns a status object** containing the `kind` of response and the `status` (either `'recorded'` or `'already'`).

## Gotchas

- **Avoid using `/auth/accept-tos` for policy flows.** Per commit `c70d472`, the logic for accepting terms/policies was moved to a specific `acceptAllPendingPolicies` helper to avoid using a "bogus" endpoint that doesn't exist in the current API contract.
- **Email-link flows require this call.** Recent work in `0990b5d` and `379ec4b` shows this is a bottleneck for testing "email-link" flows (like boat-crew and race-crew invites); if a test fails to transition a user state after clicking a link, check if `respondToInvite` was called with the correct decision.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token on the `ApiClient` instance.
- **Side effects**: Successful acceptance typically triggers visibility changes in the user's dashboard (e.g., the boat appearing in the "My Boats" list).

## External consumers

None known.

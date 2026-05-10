---
node_id: concorda-test::lib/api-client.ts::ApiClient.inviteCrewByEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 07560b35ec8a646174e6355f3a0d1f76c38b052f21308f4ac26d3de56be95cbf
status: current
---

# ApiClient.inviteCrewByEmail

## Purpose

The test-side helper for inviting a single user to a boat's crew via email. It wraps a POST request to the batch invite endpoint, specifically passing a single-element array to simulate a single-user invitation flow. Use this when testing the transition from an unauthenticated/uninvited state to a "pending invite" state for a specific email address.

## Invariants

- **HTTP Method/Path**: Performs a `POST` to `/api/boats/${boatId}/crew/invite-batch`.
- **Payload Structure**: The `emails` field must be an array containing exactly one string.
- **Return Shape**: Returns a Promise resolving to `{ invited: number; skipped: number; errors: string[] }`.
- **Auth**: Requires a valid bearer token on the `ApiClient` instance (typically established via `api.login`).

## Gotchas

- **Batch vs. Single**: Although this method takes a single `email` string, the underlying API expects an array (`emails: [email]`). Do not attempt to pass a raw string to the API directly; this helper abstracts that requirement.
- **Email-Link Flows**: Per commit `0990b5d`, this method is a primary driver for testing the "email-link" lifecycle (invitation -> email receipt -> acceptance). If testing the full flow, ensure the email used is one that can receive and process the link-based acceptance.

## Cross-cutting concerns

- **Auth**: Depends on the `ApiClient` having a valid session token.
- **Side effects**: Triggers the "email-link" flow, which is a prerequisite for testing the "My Schedule" and "Boats" tab visibility for the invited user.

## External consumers

- `concorda-test::tests/dashboard/cross-context-crew.spec.ts` (specifically test@8)

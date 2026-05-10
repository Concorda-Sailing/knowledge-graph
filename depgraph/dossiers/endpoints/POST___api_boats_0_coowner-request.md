---
node_id: POST::/api/boats/{0}/coowner-request
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 49609db73a64f38694f28f47236ae08af8c076b5a91c4b620c485be935b48084
status: llm_drafted
---

# POST /api/boats/{boat_id}/coowner-request

## Purpose

Allows an authenticated user to request co-ownership of a boat. This endpoint creates a `BoatCrew` entry with a `prospective` status and a `crew` role, effectively staging the user as a non-active member until an owner approves the request. This is distinct from `coowner_invite`, which is an owner-initiated action; this is a user-initiated "pull" to join a boat's management.

## Invariants

- **Requires `require_auth`** — The caller must be an authenticated user.
- **Creates a `prospective` status** — The `BoatCrew` entry is created with `status="prospective"` and `role="crew"` to prevent unauthorized read access to boat data before approval.
- **Returns a request object** — Returns a JSON object containing both the `request_id` (from the `create_request` service) and the `boat_crew_uuid`.
- **Prevents duplicate ownership** — If the user is already an `owner` of the boat, the request fails with a 400 error.

## Gotchas

- **Security/Access Control** — Per the logic in `request_coowner`, the user is added as a `prospective` member rather than an active one. This prevents a user from hitting this endpoint to gain immediate access to a boat's private data (punchlists, events, etc.) before an owner has vetted them.
- **Eligibility Timing** — Per commit `4c7de14`, eligibility for boat ownership is not checked at the time of the request, but rather when the request is eventually accepted. This allows the UI to handle the "upgrade" flow via the Membership tab if the user is not yet eligible.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user).
- **Side effects**: Triggers the `create_request` service to generate a `boat_coowner_promotion` request type.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.requestCoowner` (Web client)
- `concorda-test::lib/api-client.ts::ApiClient.requestCoowner` (Test suite)

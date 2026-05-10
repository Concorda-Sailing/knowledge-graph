---
node_id: concorda-test::lib/api-client.ts::ApiClient.updateBoatResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aee6b5813979a3190b6785a7d0a81b773bea4129e79dffe7d9181c0846bf9eca
status: llm_drafted
---

# ApiClient.updateBoatResume

## Purpose

Updates the specific "resume" data associated with a single boat. This is distinct from `updateBoat`, which modifies general boat properties; `updateBoatResume` targets the specialized profile data (likely historical or performance-based) tied to a specific `boatId`. Use this when a test needs to simulate updating a boat's specific credentials or-status-related metadata.

## Invariants

- **Method is `PUT`** — Uses the `this.put` method to perform a full update of the resource.
- **Endpoint path** — Targets `/api/profile/boats/${boatId}/resume`.
- **Requires `boatId`** — The first argument must be a valid string representing the boat's unique identifier.
- **Payload structure** — The `data` argument is a `Record<string, unknown>`, allowing for flexible schema updates to the resume object.

## Gotchas

- **Test host connectivity** — Per commit `917acfe`, the API client must be explicitly pointed at the remote test host rather than defaulting to localhost to avoid connection failures in CI environments.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token established via `ApiClient.login`.
- **Side effects**: Updates to the boat resume may affect how the boat is represented in the "Boats" tab or other profile-related views.

## External consumers

None known.

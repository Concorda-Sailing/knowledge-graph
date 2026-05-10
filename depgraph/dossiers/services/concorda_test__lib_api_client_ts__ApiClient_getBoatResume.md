---
node_id: concorda-test::lib/api-client.ts::ApiClient.getBoatResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ddf75a5192e3a75ff7ebb63c848e32b88b3fbb0f07f8fc21fd0a37d365369ec8
status: llm_drafted
---

# ApiClient.getBoatResume

## Purpose

Fetches the specific "Boat Resume" data for a given boat. This is used to retrieve the detailed profile information (beyond basic boat metadata) associated with a specific `boatId`. It is distinct from `getSailingResume`, which retrieves the user's personal sailing profile, and `getBoats`, which returns general boat lists.

## Invariants

- **Method is GET** — performs a read-only fetch of the boat's profile.
- **Path is resource-specific** — follows the pattern `/api/profile/boats/${boatId}/resume`.
- **Returns a Record** — the response is a `Record<string, unknown>` containing the structured resume data.
- **Requires a valid `boatId`** — the ID must be a valid string representing the target vessel.

## Gotchas

- **Requires authenticated session** — as a profile-related endpoint, it relies on the bearer token established via `ApiClient.login`.
- **Dependency on `boat_uuid` for Captain mode** — per the documentation in `addRegattasToSchedule`, certain profile-related actions (like adding regattas) depend on the caller having a `boat_uuid` set; if the resume data is missing or the ID is incorrect, downstream "Captain mode" logic in tests will fail.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token (typically established via `ApiClient.login`).
- **Side effects**: Changes to this data via `updateBoatResume` (sibling method) will affect the profile view in the user's dashboard.

## External consumers

None known.

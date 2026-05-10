---
node_id: concorda-test::lib/api-client.ts::ApiClient.updateSailingResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4cb4fa69dc274831ebc1c0fca34bbd714bcfff049b366ad856be88c4254318ee
status: llm_drafted
---

# ApiClient.updateSailingResume

## Purpose

Updates the user's sailing resume via a `PUT` request to the `/api/profile/sailing-resume` endpoint. This is a specialized helper for the `ApiClient` to modify personal profile data, distinct from the boat-specific resume updates handled by `getBoatResume`.

## Invariants

- **HTTP Method is `PUT`** — The method must use `PUT` to replace the existing resume data.
- **Input is a `Record<string, unknown>`** — The `data` object must match the expected schema for the user's sailing profile.
- **Returns `Promise<unknown>`** — The return value is the response from the server, typically used to confirm the update was successful.

## Gotchas

- **API endpoint is global, not boat-specific** — Unlike `getBoatResume` which takes a `boatId`, this method hits the base `/api/profile/sailing-resume` path. Ensure the caller understands this updates the user's general profile, not a specific vessel's data.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token established via `ApiClient.login`.
- **Side effects**: Updates to the sailing resume may affect how the user is presented in crew-finder or profile-viewing components.

## External consumers

- `concorda-test::tests/auth/crew-signup-flow.spec.ts` (used in crew-signup-flow.spec.ts:71)

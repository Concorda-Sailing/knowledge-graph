---
node_id: PUT::/api/profile/boats/{0}/resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 31ab76ad571e7a08bd2df7c93bcda4e10068b2d736b619028a233e83d73b0b90
status: current
---

# PUT /api/profile/boats/{boat_id}/resume

## Purpose

Performs an upsert (create or update) operation on a boat's public-facing resume. This endpoint allows a user to manage the descriptive metadata (about, ethos, availability, etc.) for a specific boat. It is distinct from general boat configuration as it focuses on the "resume" aspect—the public-facing profile used for crew recruitment and visibility.

## Invariants

- **Method is `PUT`** — Acts as an upsert; if a `BoatResume` record does not exist for the `boat_id`, a new one is created.
- **Ownership is mandatory** — Uses `_owner_query` to ensure the `current_user` has ownership rights over the `boat_id` before any write is permitted.
- **Strict field filtering** — Only keys defined in `BOAT_RESUME_ALLOWED_FIELDS` are persisted to the database.
- **Returns `BoatResumeRead`** — The response is the serialized model of the updated or created resume.

## Gotchas

- **Nested dictionary serialization** — The `availability` field must be explicitly converted via `.model_dump()` if it is passed as a model object, otherwise, the database write may fail or store incorrect types.
- **Cascading side effects** — Per commit `31aa70d`, changes to boat configuration (like `positions_needed`) may require cascading edits to related snapshots or assignments.
- **Ownership validation** — The endpoint relies on `_owner_query` to prevent IDOR; if the user is not the owner, a `403 Forbidden` is raised.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and passes the `current_user` to the ownership check.
- **Websocket**: Emits `BOAT_RESUME_UPDATED` via `broadcast_event` upon successful commit.
- **Audit**: N/A.
- **Rate limit**: None specific to this endpoint, but subject to general API rate limiting.
- **Side effects**: Updates the boat's public profile/resume, which may affect how the boat is displayed in crew-seeking views.

## External consumers

- `concorda-web` (via `profileApi.updateBoatResume`)
- `concorda-test` (via `ApiClient.updateBoatResume`)

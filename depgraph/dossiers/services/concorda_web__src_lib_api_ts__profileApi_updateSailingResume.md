---
node_id: concorda-web::src/lib/api.ts::profileApi.updateSailingResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e0c935bce10c3d3535d8e45a1e17eef70cd6b5627adc8d7b41c550ce2a90d463
status: current
---

# profileApi.updateSailingResume

## Purpose

Updates the user's personal sailing resume via a `PUT` request. This is the primary method for a user to modify their professional/personal sailing history (experience, certifications, etc.) within their profile. It is distinct from `updateBoatResume`, which manages the specific sailing history associated with a particular vessel.

## Invariants

- **HTTP Method is `PUT`** — Uses the standard idempotent update pattern for the `/api/profile/sailing-resume` endpoint.
- **Requires `SailingResumeUpdate` payload** — The input must match the expected shape of the user's sailing history.
- **Returns `SailingResume`** — On success, the method returns the updated object, allowing the UI to refresh the local state immediately.
- **Authenticated** — Uses `fetchApiAuthenticated` to ensure the request is tied to the current user's session.

## Gotchas

- **Relationship to Boat Resumes** — Users often confuse the personal "Sailing Resume" with "Boat Resumes." While `updateSailingResume` updates the global user profile, `updateBoatResume` (see `profileApi.updateBoatResume`) is used for vessel-specific histories.
- **Schema dependency** — Changes to the `SailingResume` shape in the backend will require a corresponding update to the `SailingResumeUpdate` type to avoid runtime failures during `JSON.stringify(data)`.

## Cross-cutting concerns

- **Auth**: Requires a valid session via `fetchApiAuthenticated`.
- **Side effects**: Updates to the sailing resume may affect how a user's experience is displayed in directory-facing components or crew-finding views.

## External consumers

None known.

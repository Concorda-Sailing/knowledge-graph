---
node_id: GET::/api/profile/boat-resumes
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3f7d7c492e16fa2328b6a784849b89d76589eb5d8671f3a024ce1422eab7b792
status: current
---

# GET /api/profile/boat-resumes

## Purpose

Retrieves a list of all `BoatResume` objects associated with boats owned by the authenticated user. This is a bulk retrieval endpoint used to populate overview lists in the profile section, distinct from the single-boat retrieval endpoint which requires a specific `boat_id`.

## Invariants

- **Method is `GET`** and returns a JSON array of `BoatResumeRead` objects.
- **Auth is mandatory** via the `require_auth` dependency.
- **Ownership is strictly enforced**; the result set is limited to boats where the `current_user.id` is identified as an owner via `_owned_boat_ids`.
- **Returns an empty list `[]`** if the user owns no boats or no resumes exist, rather than a 404.

## Gotchas

- **IDOR Protection:** Following the `c9a7c41` security audit, this endpoint relies on the `_owned_boat_ids` helper to ensure users cannot scrape resumes for boats they do not own.
- **Data Schema Evolution:** Recent commits `f311f7a` and `edc7e22` added fields for US/World Sailing credentials and `preferred_oa_ids`. Ensure any consumer of this list is prepared for these new fields in the `BoatResumeRead` model.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `concorda-web` (via `profileApi.getBoatResumes`)

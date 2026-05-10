---
node_id: GET::/api/profile/boats/{0}/resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a3b99c351177b4fcf43cad40d4278807eac9591d56fd0b37fdcf976b862466e0
status: current
---

# GET /api/profile/boats/{boat_id}/resume

## Purpose

Retrieves the `BoatResume` object for a specific boat. This is a read-only view of a boat's profile, including its ethos, crew complement, and positions. It is distinct from the `upsert` endpoint, which handles the creation and modification of this data.

## Invariants

- **Requires `require_auth`** — The caller must be authenticated.
- **Ownership check is mandatory** — The request must pass the `_owner_query` check; users can only retrieve resumes for boats they own.
- **Returns `BoatResumeRead`** — The response shape is strictly defined by the `BoatResumeRead` model.
- **Throws 404 if boat or resume is missing** — If the `boat_id` does not exist or no `BoatResume` record is linked to it, the API returns a 404.

## Gotchas

- **Ownership verification is strict** — Per commit `c9a7c41` (security: tier-A IDOR audit fixes), this endpoint relies on `_owner_query` to prevent unauthorized users from accessing boat details via ID guessing.
- **Credential fields are specialized** — Recent changes in `edc7e22` and `af14e8c` added support for US/World Sailing credential fields and `preferred_oa_ids`. Ensure any consumer of this data is aware that the resume structure includes these specific sailing-related fields.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and `_owner_query` to enforce ownership-based access control.
- **Side effects**: Changes to the boat's resume (via the sibling `PUT` endpoint) are intended to be the source of truth for the boat's profile display in the web UI.

## External consumers

- `concorda-web` (via `profileApi.getBoatResume`)
- `concorda-test` (via `ApiClient.getBoatResume`)

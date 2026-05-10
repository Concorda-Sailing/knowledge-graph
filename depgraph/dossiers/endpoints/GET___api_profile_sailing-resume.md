---
node_id: GET::/api/profile/sailing-resume
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eb17a0278f38166ef6ea3f2339d6ec57255953ce6eb83967aced4630027c1376
status: current
---

# GET /api/profile/sailing-resume

## Purpose

Retrieves the current user's sailing resume profile. This endpoint is the primary source of truth for a user's sailing experience, credentials, and availability, used to populate user profiles and potentially influence crew matching logic. It is distinct from the `PUT` version of the same path, which handles the upsert logic.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a `SailingResumeRead` object** containing the user's experience, certifications, and availability.
- **Returns a 404 error** if no record exists for the `current_user.id`.
- **Data is tied to `person_id`**, ensuring users can only access their own profile.

## Gotchas

- **Field allowlist is strict.** Per commit `edc7e22`, the `upsert` logic (which this GET endpoint serves as the read-side for) uses a hardcoded `SAILING_RESUME_ALLOWED_FIELDS` set. If a new field is added to the model but not this list, it will be silently dropped during updates.
- **Credential fields are recent additions.** Commit `f311f7a` added US/World Sailing credential fields; ensure any logic consuming this endpoint accounts for these specific identity fields.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the `current_user` is identified.
- **Websocket**: While this is a GET endpoint, the sibling `PUT` method broadcasts `SAILING_RESUME_UPDATED` to the `current_user.id`.
- **Side effects**: Updates to the resume (via the sibling `PUT`) may affect how a user appears in crew-related searches or profile views.

## External consumers

- `concorda-web` (via `profileApi.getSailingResume`)
- `concorda-test` (via `ApiClient.getSailingResume`)

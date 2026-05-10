---
node_id: PUT::/api/crewfinder/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: daa0d3ec6b48a49af750174c78e3b726e0400e3434a36aeddc95cc2a15f76de4
status: current
---

# PUT /api/crewfinder/{resume_id}

## Purpose

Updates an existing user's sailing resume. This endpoint is distinct from the creation endpoint as it implements a strict allow-list for field updates to prevent accidental modification of sensitive or immutable fields (like `person_id`). Use this when a user is editing their profile details in the Crew Finder settings.

## Invariants

- **Method is `PUT`** and requires a valid `resume_id` in the path.
- **Ownership check is mandatory.** The `current_user.id` must match the `db_resume.person_id` or a 403 error is raised.
- **Field-level restriction.** Only fields defined in `SAILING_RESUME_ALLOWED_FIELDS` can be updated; any other keys in the request body are ignored.
- **Returns `SailingResumeRead` schema.** The response includes the fully updated object, including the immutable `person_id`.

## Gotchas

- **Strict field filtering.** Unlike the creation endpoint, this method uses `SAILING_RESUME_ALLOWED_FIELDS` to filter `update_data`. If a new field is added to the `SailingResume` model but not this list, it will be silently ignored during updates.
- **Security/PII protection.** Per commit `33a37a3`, this endpoint is part of the hardened security layer to prevent privilege gaps. Attempting to update the `person_id` or other restricted fields via this endpoint will fail to change them due to the `setattr` loop logic.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` dependency; requires a valid user session.
- **Audit**: N/A.
- **Side effects**: Updates to `experience_level` or `boat_classes_sailed` may affect how the user appears in search results for boat owners/organizers.

## External consumers

- Web frontend (Crew Finder profile edit forms).

## Open questions

- Should the `SAILING_RESUME_ALLOWED_FIELDS` list be moved to a central schema constant to ensure the creation and update endpoints stay in sync?

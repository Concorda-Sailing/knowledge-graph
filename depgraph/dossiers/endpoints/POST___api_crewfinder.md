---
node_id: POST::/api/crewfinder
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b9b6f3673d01feae9c4342bdbc4450f3dbbdcc5035d140c055a37dd6f77f374a
status: llm_drafted
---

# POST /api/crewfinder

## Purpose

Creates a new user's sailing resume (crew profile) within the system. This endpoint is used to transition a user from a standard account to a "crew-ready" profile, allowing them to be discoverable by boat owners. It is distinct from the `PUT` method in that it handles the initial creation and enforces a strict "one-resume-per-person" rule to prevent duplicate profiles.

## Invariants

- **Requires `require_auth`** — The `current_user` is automatically injected via the dependency, and the `person_id` is tied to the authenticated user's ID.
- **Returns `SailingResumeRead`** — The response shape is a serialized version of the created object, including the generated `id`.
- **Single-entry constraint** — A user cannot have more than one active resume; attempting to create a second one results in a 400 error.
- **Field exclusion** — The `person_id` is not accepted in the request body; it is strictly derived from the `current_user.id` to prevent identity spoofing.

## Gotchas

- **PII/Privilege Gaps** — Per commit `33a37a3`, this endpoint and its related logic were part of a security hardening effort to ensure users cannot inadvertently expose sensitive data or escalate privileges through the crew profile.
- **Strict field white-listing** — The `update_sailing_resume` logic (the sibling `PUT` method) uses `SAILING_RESUME_ALLOWED_FIELDS` to prevent arbitrary field injection. If you add a new field to the `SailingResume` model, you must manually add it to this set in the router to ensure it is updatable.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the creator.
- **Audit**: N/A.
- **Side effects**: Populates data used by the "crew finder" detail pages and boat owner discovery views.

## External consumers

- Web frontend (user profile/onboarding flows).
